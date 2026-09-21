# KAB Attendance Registry

The roster/check-in module is implemented in Python and stores data locally in
`attendance_log.json`. It supports creating student profiles, recording a
daily `Present` or `Late` check-in, and listing students checked in today.

## Run

```text
python app.py
```

The JSON file is created automatically the first time a student profile is
saved. Run the roster tests with:

```text
python -m unittest -v
```

The reporting module will be integrated separately on its own feature branch.