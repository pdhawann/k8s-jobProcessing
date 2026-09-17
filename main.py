import json 
import uuid
import redis
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

app = FastAPI(title="KubeOps Job Processing API")

redis_client=redis.Redis(host="localhost",port=6379,decode_responses=True,socket_timeout=None,
    socket_connect_timeout=5)

class JobRequest(BaseModel):
    type: str
    duration: int=5

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    try: 
        redis_client.ping()
        return {"status": "ready"}
    except redis.RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.post("/jobs")
def create_job(job: JobRequest):

    job_id=str(uuid.uuid4())

    job_data={
        "job_id": job_id,
        "job_type": job.type,
        "job_duration": job.duration,
        "job_status": "queued"
    }

    with redis_client.pipeline() as pipe:
        pipe.hset(f"job:{job_id}", mapping=job_data)
        pipe.rpush("job_queue", json.dumps({"job_id": job_id}) )
        pipe.execute()

    return{
        "job_id": job_id,
        "job_status": "queued"
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job= redis_client.hgetall(f"job:{job_id}")
    if not job:
        raise HTTPException(status=404,detail="Job not found")

    return job

@app.get("/jobs")
def get_jobs():
    keys=redis_client.keys("job:*")
    jobs=[]

    for key in keys:
        jobs.append(redis_client.hgetall(key))

    return jobs