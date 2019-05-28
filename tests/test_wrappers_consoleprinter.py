import pytest

from types import SimpleNamespace

from ruamel.yaml.scalarstring import PlainScalarString

from yamlpath.wrappers import ConsolePrinter

class Test_wrappers_ConsolePrinter():
    def test_info_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.info("Test")
        console = capsys.readouterr()
        assert console.out == "Test\n"

    def test_info_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.info("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_verbose_off(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.verbose("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_verbose_noisy(self, capsys):
        args = SimpleNamespace(verbose=True, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.verbose("Test")
        console = capsys.readouterr()
        assert console.out == "Test\n"

    def test_verbose_quiet(self, capsys):
        args = SimpleNamespace(verbose=True, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.verbose("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_debug_off(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.debug("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_debug_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        anchoredval = PlainScalarString("Test", anchor="Anchor")

        logger.debug(anchoredval)
        console = capsys.readouterr()
        assert console.out == "DEBUG:  Test; &Anchor\n"

        logger.debug(["test", anchoredval])
        console = capsys.readouterr()
        assert console.out == "DEBUG:  [0]=test\nDEBUG:  [1]=Test; &Anchor\n"

        logger.debug({"ichi": 1, "test": anchoredval})
        console = capsys.readouterr()
        assert console.out == "DEBUG:  [ichi]=>1\nDEBUG:  [test]=>Test; &Anchor\n"

    def test_debug_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=True)
        logger = ConsolePrinter(args)
        logger.debug("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_warning_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.warning("Test")
        console = capsys.readouterr()
        assert console.out == "WARNING:  Test\n"

    def test_warning_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.warning("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_error_noisy_nonexit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.error("Test")
        console = capsys.readouterr()
        assert console.err == "ERROR:  Test\n"

    def test_error_quiet_nonexit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.error("Test")
        console = capsys.readouterr()
        assert console.err == "ERROR:  Test\n"

    def test_error_noisy_exit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.error("Test", 27)
            console = capsys.readouterr()
            assert console.err == "ERROR:  Test\n"

    def test_error_quiet_exit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.error("Test", 27)
            console = capsys.readouterr()
            assert console.err == "ERROR:  Test\n"

    def test_critical_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.critical("Test")
            console = capsys.readouterr()
            assert console.err == "CRITICAL:  Test\n"

    def test_critical_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.critical("Test")
            console = capsys.readouterr()
            assert console.err == "CRITICAL:  Test\n"
