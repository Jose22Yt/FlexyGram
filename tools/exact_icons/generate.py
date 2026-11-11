#!/usr/bin/env python3
"""Compatibility entry point: the default now uses original Telegram-iOS resources."""
import pathlib,runpy,sys
path=pathlib.Path(__file__).resolve().parents[1]/'ios_originals'
sys.path.insert(0,str(path))
runpy.run_path(str(path/'generate.py'),run_name='__main__')
