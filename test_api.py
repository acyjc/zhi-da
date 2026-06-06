import json, urllib.request, sys

def get(path):
    try:
        resp = urllib.request.urlopen(f'http://localhost:8000{path}')
        return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def post(path, data=None):
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(f'http://localhost:8000{path}', data=body, headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

errors = []

print('1. Health')
r = get('/api/health')
if r.get('status') != 'ok':
    errors.append(f'Health failed: {r}')
print(f'   OK: {r}')

print('2. GET /api/jobs')
jobs = get('/api/jobs')
if isinstance(jobs, list) and len(jobs) == 5:
    j = jobs[0]
    print(f'   OK: {len(jobs)} jobs, first={j["title"]} location={j.get("location","-")} review={j.get("school_review_status","-")}')
else:
    errors.append(f'Jobs failed: {jobs}')
    print(f'   FAIL: {jobs}')

print('3. GET /api/school/dashboard')
d = get('/api/school/dashboard')
if 'total_students' in d:
    print(f'   OK: students={d["total_students"]} jobs={d["total_jobs"]} enterprises={d["total_enterprises"]} courses={d["course_count"]}')
else:
    errors.append(f'Dashboard failed: {d}')
    print(f'   FAIL: {d}')

print('4. GET /api/school/courses')
courses = get('/api/school/courses')
if isinstance(courses, list) and len(courses) == 5:
    print(f'   OK: {len(courses)} courses')
    for c in courses[:2]:
        print(f'     {c["name"]} | {c["status"]}')
else:
    errors.append(f'Courses failed: {courses}')
    print(f'   FAIL: {courses}')

print('5. GET /api/enterprise/jobs')
ejobs = get('/api/enterprise/jobs')
if isinstance(ejobs, list) and len(ejobs) == 5:
    print(f'   OK: {len(ejobs)} enterprise jobs')
else:
    errors.append(f'Enterprise jobs failed: {ejobs}')
    print(f'   FAIL: {ejobs}')

print('6. GET /api/enterprise/dashboard')
ed = get('/api/enterprise/dashboard')
if 'total_jobs' in ed:
    print(f'   OK: total_jobs={ed["total_jobs"]} authorized={ed["authorized_candidates"]}')
else:
    errors.append(f'Enterprise dashboard failed: {ed}')
    print(f'   FAIL: {ed}')

print('7. POST /api/students (old student API)')
student = post('/api/students', {"name": "测试学生", "grade": "大三", "major": "计算机科学", "target_job": "Python后端开发工程师"})
if 'id' in student:
    sid = student['id']
    print(f'   OK: student created id={sid}')
    
    print('8. GET /api/students/{id}')
    s = get(f'/api/students/{sid}')
    if s.get('name') == '测试学生':
        print(f'   OK: got student {s["name"]}')
    else:
        errors.append(f'Get student failed: {s}')
        print(f'   FAIL: {s}')
else:
    errors.append(f'Create student failed: {student}')
    print(f'   FAIL: {student}')

print('\n' + '='*50)
if errors:
    print(f'FAILED: {len(errors)} errors')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('ALL TESTS PASSED!')
