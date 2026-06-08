#!/bin/sh

pip3 install -r requirements.txt

pytest --junitxml=testreport.xml --cov --cov-report xml:coverage.xml --cov-report=html:coverage_report