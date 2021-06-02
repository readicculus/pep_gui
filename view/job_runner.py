
# Given a job directory, load the job and start/resume running
from core.job import load_job
from settings import get_settings


def run_job(job_path: str):
    settings = get_settings()
    job_state, job_meta = load_job(job_path)
    pass

if __name__ == '__main__':
    # TODO: open job selection GUI
    run_job('/home/yuval/Desktop/jobs/test')