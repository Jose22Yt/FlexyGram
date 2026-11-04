#!/usr/bin/env python3
"""Production Floating geometry, Android layout and photo masks; native services are explicit doubles. No APK."""
from run import pipeline, resources, HERE
from stubs import write_stubs

if __name__ == '__main__':
    raise SystemExit(pipeline.main(here=HERE, test_class='FloatingHeaderTest',
                                 stubs_writer=write_stubs, resource_writer=resources))
