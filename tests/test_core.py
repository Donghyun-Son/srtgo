import os, sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch

from srtgo import core


def test_set_login_credentials_success():
    with patch.object(core, 'SRT') as srt_cls, patch.object(core, 'keyring') as kr:
        assert core.set_login_credentials('SRT', 'uid', 'pwd') is True
        srt_cls.assert_called_with('uid', 'pwd', verbose=False)
        kr.set_password.assert_any_call('SRT', 'id', 'uid')
        kr.set_password.assert_any_call('SRT', 'pass', 'pwd')


def test_set_login_credentials_failure():
    with patch.object(core, 'SRT', side_effect=Exception), patch.object(core, 'keyring') as kr:
        assert core.set_login_credentials('SRT', 'uid', 'pwd') is False
        kr.set_password.assert_not_called()


def test_search_trains():
    stub = SimpleNamespace(search_train=lambda d, a, dt, tm: ['t'])
    with patch.object(core, 'login', return_value=stub) as login_mock:
        result = core.search_trains('SRT', 'A', 'B', '20230101', '0000')
        assert result == ['t']
        login_mock.assert_called_once_with('SRT')


def test_reserve_train_with_pay():
    rail = SimpleNamespace(
        search_train=lambda *args, **kwargs: ['train'],
        reserve=lambda *args, **kwargs: SimpleNamespace(is_waiting=False)
    )
    with (
        patch.object(core, 'login', return_value=rail),
        patch.object(core, '_build_passengers', return_value=['p']),
        patch.object(core, '_cli_pay_card') as pay_mock
    ):
        core.reserve_train('SRT', 'A', 'B', '20230101', '0900', pay=True)
        pay_mock.assert_called_once()


def test_reserve_train_no_trains():
    rail = SimpleNamespace(search_train=lambda *args, **kwargs: [])
    with patch.object(core, 'login', return_value=rail):
        with pytest.raises(RuntimeError):
            core.reserve_train('SRT', 'A', 'B', '20230101', '0000')
