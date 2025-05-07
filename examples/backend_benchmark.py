import dis
import time
import json
import orjson
import ujson
import rapidjson
import simplejson
import ijson
from io import BytesIO, StringIO

def recursive_nested_dict(levels: int, current_level: int = 0):
    if current_level >= levels:
        return {}
    return {
        f"level_{current_level}": recursive_nested_dict(levels, current_level + 1)
    }

# Generate sample data: a list of dicts
def generate_sample(n_items=300000, n_values=120, levels: int = 7):
    return [
        {
            "id": i,
            "name": f"item_{i}",
            "values": list(range(n_values)),
            "nested": {"flag": True, "score": i * 0.1},
            "deeply_nested": recursive_nested_dict(levels),
        }
        for i in range(n_items)
    ]

# Benchmark configurations
iterations = 10

def bench_load(name, load_func, data):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        load_func(data)
        end = time.perf_counter()
        times.append(end - start)
    avg_time = sum(times) / iterations
    print(f"{name:12} load avg: {avg_time:.4f}s over {iterations} iterations")

def bench_dump(name, dump_func, data):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        dump_func(data)
        end = time.perf_counter()
        times.append(end - start)
    avg_time = sum(times) / iterations
    print(f"{name:12} dump avg: {avg_time:.4f}s over {iterations} iterations")

if __name__ == "__main__":
    base = {
        "n_items": 10000,
        "n_values": 30,
        "levels": 8
    }
    for factor in range(0, 15):
        input_data = {k: int(value**(1+factor/20)) for k, value in base.items()}
        print(f"\nSample data input: {input_data}")
        # Prepare data
        sample_data = generate_sample(**input_data)
        print(f"Memory size of sample data: {len(json.dumps(sample_data))/1024**2} mb")
        json_str = json.dumps(sample_data)
        json_bytes = json_str.encode("utf-8")

        print("\n=== JSON Load Benchmarks ===")
        bench_load("stdlib json", lambda b: json.loads(b if isinstance(b, str) else b.decode()), json_str)
        bench_load("orjson     ", lambda b: orjson.loads(b if isinstance(b, bytes) else b.encode()), json_bytes)
        bench_load("ujson      ", lambda b: ujson.loads(b if isinstance(b, str) else b.decode()), json_str)
        bench_load("rapidjson  ", lambda b: rapidjson.loads(b if isinstance(b, str) else b.decode()), json_str)
        bench_load("simplejson ", lambda b: simplejson.loads(b), json_str)

        # ijson streaming load: count elements
        def ijson_load(data):
            count = 0
            for _ in ijson.items(BytesIO(data.encode()), ''):
                count += 1
            return count
        # bench_load("ijson      ", ijson_load, json_str)

        print("\n=== JSON Dump Benchmarks ===")
        bench_dump("stdlib json", lambda d: json.dumps(d), sample_data)
        bench_dump("orjson     ", lambda d: orjson.dumps(d), sample_data)
        bench_dump("ujson      ", lambda d: ujson.dumps(d), sample_data)
        bench_dump("rapidjson  ", lambda d: rapidjson.dumps(d), sample_data)
        bench_dump("simplejson ", lambda d: simplejson.dumps(d), sample_data)
        # ijson has no dump
        # print("ijson      dump: n/a (parser only)")
