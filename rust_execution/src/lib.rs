//! SIGMAX Ultra-Low-Latency Rust Execution Engine

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

#[derive(Clone)]
#[pyclass]
pub struct RustExecution {
    #[pyo3(get)]
    pub order_id: u64,
    #[pyo3(get)]
    pub executed_price: f64,
    #[pyo3(get)]
    pub executed_quantity: f64,
    #[pyo3(get)]
    pub latency_ns: u64,
    #[pyo3(get)]
    pub slippage: f64,
}

#[pymethods]
impl RustExecution {
    fn to_dict(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("order_id", self.order_id)?;
            dict.set_item("executed_price", self.executed_price)?;
            dict.set_item("executed_quantity", self.executed_quantity)?;
            dict.set_item("latency_ns", self.latency_ns)?;
            dict.set_item("slippage", self.slippage)?;
            Ok(dict.into())
        })
    }
}

#[pyclass]
pub struct RustExecutionEngine {
    next_order_id: AtomicU64,
    total_executions: AtomicU64,
    total_latency_ns: AtomicU64,
    min_latency_ns: AtomicU64,
    max_latency_ns: AtomicU64,
}

#[pymethods]
impl RustExecutionEngine {
    #[new]
    pub fn new() -> Self {
        Self {
            next_order_id: AtomicU64::new(1),
            total_executions: AtomicU64::new(0),
            total_latency_ns: AtomicU64::new(0),
            min_latency_ns: AtomicU64::new(u64::MAX),
            max_latency_ns: AtomicU64::new(0),
        }
    }

    #[inline(always)]
    pub fn execute_order(
        &self,
        symbol_id: u32,
        side: u8,
        order_type: u8,
        price: f64,
        quantity: f64,
    ) -> PyResult<RustExecution> {
        let start = Instant::now();

        let order_id = self.next_order_id.fetch_add(1, Ordering::Relaxed);

        let (executed_price, executed_quantity, slippage) = 
            Self::execute_internal(price, quantity, side, order_type);

        let latency_ns = start.elapsed().as_nanos() as u64;

        self.update_stats(latency_ns);

        Ok(RustExecution {
            order_id,
            executed_price,
            executed_quantity,
            latency_ns,
            slippage,
        })
    }

    pub fn get_stats(&self) -> PyResult<PyObject> {
        let total_executions = self.total_executions.load(Ordering::Relaxed);
        let total_latency = self.total_latency_ns.load(Ordering::Relaxed);
        let min_latency = self.min_latency_ns.load(Ordering::Relaxed);
        let max_latency = self.max_latency_ns.load(Ordering::Relaxed);

        let avg_latency = if total_executions > 0 {
            total_latency / total_executions
        } else {
            0
        };

        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("total_executions", total_executions)?;
            dict.set_item("avg_latency_ns", avg_latency)?;
            dict.set_item("min_latency_ns", if min_latency == u64::MAX { 0 } else { min_latency })?;
            dict.set_item("max_latency_ns", max_latency)?;
            Ok(dict.into())
        })
    }

    pub fn reset_stats(&self) {
        self.total_executions.store(0, Ordering::Relaxed);
        self.total_latency_ns.store(0, Ordering::Relaxed);
        self.min_latency_ns.store(u64::MAX, Ordering::Relaxed);
        self.max_latency_ns.store(0, Ordering::Relaxed);
    }
}

impl RustExecutionEngine {
    #[inline(always)]
    fn execute_internal(
        price: f64,
        quantity: f64,
        side: u8,
        order_type: u8
    ) -> (f64, f64, f64) {
        let executed_price = if order_type == 1 {
            price
        } else {
            price
        };

        let slippage = if side == 0 { 0.0001 } else { -0.0001 };
        let executed_quantity = quantity;

        (executed_price, executed_quantity, slippage)
    }

    #[inline(always)]
    fn update_stats(&self, latency_ns: u64) {
        self.total_executions.fetch_add(1, Ordering::Relaxed);
        self.total_latency_ns.fetch_add(latency_ns, Ordering::Relaxed);

        let mut current_min = self.min_latency_ns.load(Ordering::Relaxed);
        while latency_ns < current_min {
            match self.min_latency_ns.compare_exchange_weak(
                current_min,
                latency_ns,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(x) => current_min = x,
            }
        }

        let mut current_max = self.max_latency_ns.load(Ordering::Relaxed);
        while latency_ns > current_max {
            match self.max_latency_ns.compare_exchange_weak(
                current_max,
                latency_ns,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(x) => current_max = x,
            }
        }
    }
}

#[pyfunction]
pub fn execute_batch(
    engine: &RustExecutionEngine,
    orders: Vec<(u32, u8, u8, f64, f64)>,
) -> PyResult<Vec<RustExecution>> {
    let mut executions = Vec::with_capacity(orders.len());

    for (symbol_id, side, order_type, price, quantity) in orders {
        let execution = engine.execute_order(
            symbol_id,
            side,
            order_type,
            price,
            quantity,
        )?;
        executions.push(execution);
    }

    Ok(executions)
}

#[pyfunction]
pub fn benchmark_latency(iterations: usize) -> PyResult<PyObject> {
    let engine = RustExecutionEngine::new();

    let mut latencies: Vec<u64> = Vec::with_capacity(iterations);

    for _ in 0..100 {
        let _ = engine.execute_order(1, 0, 0, 50000.0, 1.0);
    }

    engine.reset_stats();

    for _ in 0..iterations {
        let execution = engine.execute_order(1, 0, 0, 50000.0, 1.0)?;
        latencies.push(execution.latency_ns);
    }

    latencies.sort_unstable();
    let p50 = latencies[iterations / 2];
    let p95 = latencies[iterations * 95 / 100];
    let p99 = latencies[iterations * 99 / 100];
    let min = latencies[0];
    let max = latencies[iterations - 1];
    let avg: u64 = latencies.iter().sum::<u64>() / iterations as u64;

    Python::with_gil(|py| {
        let dict = PyDict::new(py);
        dict.set_item("iterations", iterations)?;
        dict.set_item("avg_ns", avg)?;
        dict.set_item("min_ns", min)?;
        dict.set_item("max_ns", max)?;
        dict.set_item("p50_ns", p50)?;
        dict.set_item("p95_ns", p95)?;
        dict.set_item("p99_ns", p99)?;
        Ok(dict.into())
    })
}

#[pymodule]
fn sigmax_rust_execution(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustExecutionEngine>()?;
    m.add_class::<RustExecution>()?;
    m.add_function(wrap_pyfunction!(execute_batch, m)?)?;
    m.add_function(wrap_pyfunction!(benchmark_latency, m)?)?;
    Ok(())
}
