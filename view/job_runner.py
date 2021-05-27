
# Given a job directory, load the job and start/resume running
from core.job import load_job


def run_job(job_path: str):
    job_state = load_job(job_path)
    pass

if __name__ == '__main__':
    # TODO: open job selection GUI
    pass