from pathlib import Path

import pytest

from macwise.persistence import StateLock, StateLockError


def test_state_lock_excludes_a_second_writer_and_releases_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "state" / "macwise.lock"

    with StateLock(path):
        assert path.is_file()
        with (
            pytest.raises(StateLockError, match="another MacWise change is in progress"),
            StateLock(path),
        ):
            raise AssertionError("a second writer acquired the same lock")

    with StateLock(path):
        assert path.is_file()


def test_state_lock_rejects_symlink_ancestors_without_creating_outside_state(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(outside, target_is_directory=True)

    with (
        pytest.raises(StateLockError, match="symbolic link"),
        StateLock(link / "nested" / "macwise.lock"),
    ):
        raise AssertionError("unsafe lock acquired")

    assert not (outside / "nested").exists()
