#!/usr/bin/env bash

cmd=(
  pytest dev_mode_test.py::test_dev_mode_with_empty_project__should_show_quickstart_dialog
  --log-format '%(asctime)s.%(msecs)03d %(levelname).1s %(name)s:%(filename)s:%(lineno)d %(message)s'
)

rm -f run1.log run2.log  # remove old log files

while true
do
  mv -f run2.log run1.log
  "${cmd[@]}" >run2.log 2>&1 || exit 1
done
