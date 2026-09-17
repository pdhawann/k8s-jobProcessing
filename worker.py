import json
import redis 
import time

redis_client=redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def process_job(job_id: str):
    job = redis_client.hgetall(f"job:{job_id}")
    if not job:
        return
    job_type = job["job_type"]
    job_duration = int(job["job_duration"])
    job_status = job["job_status"]
    if job_type=="cpu":
        start_time = time.time()
        while time.time() - start_time < job_duration:
            pass
        job_status = "completed"
    elif job_type=="sleep":
        time.sleep(job_duration)
        job_status = "completed"
    else:
        job_status = "failed"
    redis_client.hset(f"job:{job_id}", mapping={"job_status": job_status})
    return job_status

def main():
    print("Worker started")
    while True:
        _, job_data = redis_client.blpop("job_queue", timeout=0)
        job_id = json.loads(job_data)["job_id"]
        try:
            process_job(job_id)
        except Exception as e:
            redis_client.hset(
                f"job:{job_id}",
                mapping={"job_status": "failed", "result": str(e)},
            )
            print(f"Job {job_id} failed: {e}")
if __name__ == "__main__":
    main()