with open('demo/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Indent lines from 438 to 495
for i in range(438, 496):
    if i < len(lines):
        lines[i] = '    ' + lines[i]

with open('demo/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
