import pytest

from pytest_deadfixtures import (
    DUPLICATE_FIXTURES_HEADLINE,
    EXIT_CODE_ERROR,
    EXIT_CODE_SUCCESS,
)


def test_error_exit_code_on_dead_fixtures_found(testdir):
    testdir.makepyfile("""
            import pytest


            @pytest.fixture()
            def some_fixture():
                return 1
        """)

    result = testdir.runpytest('--dead-fixtures')

    assert result.ret == EXIT_CODE_ERROR


def test_success_exit_code_on_dead_fixtures_found(testdir):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def some_fixture():
            return 1


        def test_simple(some_fixture):
            assert 1 == some_fixture
    """)

    result = testdir.runpytest('--dead-fixtures')

    assert result.ret == EXIT_CODE_SUCCESS


def test_dont_list_autouse_fixture(testdir, message_template):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture(autouse=True)
        def autouse_fixture():
            return 1


        def test_simple():
            assert 1 == 1
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'autouse_fixture',
        'test_dont_list_autouse_fixture'
    )

    assert message not in result.stdout.str()

    result = testdir.runpytest('--used-fixtures')
    message = message_template.format(
        'autouse_fixture',
        'test_dont_list_autouse_fixture'
    )

    assert message in result.stdout.str()


def test_dont_list_same_file_fixture(testdir, message_template):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def same_file_fixture():
            return 1


        def test_simple(same_file_fixture):
            assert 1 == same_file_fixture
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'same_file_fixture',
        'test_dont_list_same_file_fixture'
    )

    assert message not in result.stdout.str()

    result = testdir.runpytest('--used-fixtures')
    message = message_template.format(
        'same_file_fixture',
        'test_dont_list_same_file_fixture'
    )

    assert message in result.stdout.str()


def test_list_same_file_unused_fixture(testdir, message_template):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def same_file_fixture():
            return 1


        def test_simple():
            assert 1 == 1
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'same_file_fixture',
        'test_list_same_file_unused_fixture'
    )

    assert message in result.stdout.str()

    result = testdir.runpytest('--used-fixtures')
    message = message_template.format(
        'same_file_fixture',
        'test_list_same_file_unused_fixture'
    )

    assert message not in result.stdout.str()


def test_dont_list_conftest_fixture(testdir, message_template):
    testdir.makepyfile(conftest="""
        import pytest


        @pytest.fixture()
        def conftest_fixture():
            return 1
    """)

    testdir.makepyfile("""
        import pytest


        def test_conftest_fixture(conftest_fixture):
            assert 1 == conftest_fixture
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'conftest_fixture',
        'conftest'
    )

    assert message not in result.stdout.str()

    result = testdir.runpytest('--used-fixtures')
    message = message_template.format(
        'conftest_fixture',
        'conftest'
    )

    assert message in result.stdout.str()


def test_list_conftest_unused_fixture(testdir, message_template):
    testdir.makepyfile(conftest="""
        import pytest


        @pytest.fixture()
        def conftest_fixture():
            return 1
    """)

    testdir.makepyfile("""
        import pytest


        def test_conftest_fixture():
            assert 1 == 1
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'conftest_fixture',
        'conftest'
    )

    assert message in result.stdout.str()

    result = testdir.runpytest('--used-fixtures')
    message = message_template.format(
        'conftest_fixture',
        'conftest'
    )

    assert message not in result.stdout.str()


def test_dont_list_decorator_usefixtures(testdir, message_template):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def decorator_usefixtures():
            return 1


        @pytest.mark.usefixtures('decorator_usefixtures')
        def test_decorator_usefixtures():
            assert 1 == decorator_usefixtures
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'decorator_usefixtures',
        'test_dont_list_decorator_usefixtures'
    )

    assert message not in result.stdout.str()

    result = testdir.runpytest('--used-fixtures')
    message = message_template.format(
        'decorator_usefixtures',
        'test_dont_list_decorator_usefixtures'
    )

    assert message in result.stdout.str()


def test_write_docs_when_verbose(testdir):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def some_fixture():
            '''Blabla fixture docs'''
            return 1


        def test_simple():
            assert 1 == 1
    """)

    result = testdir.runpytest('--dead-fixtures', '-v')

    assert 'Blabla fixture docs' in result.stdout.str()


def test_repeated_fixtures_not_found(testdir):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def some_fixture():
            return 1


        def test_simple(some_fixture):
            assert 1 == some_fixture
    """)

    result = testdir.runpytest('--dup-fixtures')

    assert DUPLICATE_FIXTURES_HEADLINE not in result.stdout.str()


def test_repeated_fixtures_found(testdir):
    testdir.makepyfile("""
        import pytest


        class SomeClass:
            a = 1

            def spam(self):
                return 'and eggs'


        @pytest.fixture()
        def someclass_fixture():
            return SomeClass()


        @pytest.fixture()
        def someclass_samefixture():
            return SomeClass()


        def test_simple(someclass_fixture):
            assert 1 == 1

        def test_simple_again(someclass_samefixture):
            assert 2 == 2
    """)

    result = testdir.runpytest('--dup-fixtures')

    assert DUPLICATE_FIXTURES_HEADLINE in result.stdout.str()
    assert 'someclass_samefixture' in result.stdout.str()


@pytest.mark.parametrize('directory', (
    'site-packages',
    'dist-packages',
))
def test_should_not_list_fixtures_from_unrelated_directories(
    testdir,
    message_template,
    directory,
):
    testdir.tmpdir = testdir.mkdir(directory)

    testdir.makepyfile(conftest="""
        import pytest


        @pytest.fixture()
        def conftest_fixture():
            return 1
    """)

    testdir.makepyfile("""
        import pytest


        def test_conftest_fixture():
            assert 1 == 1
    """)

    result = testdir.runpytest('--dead-fixtures')

    message = message_template.format(
        'conftest_fixture',
        '{}/conftest'.format(directory),
    )

    assert message not in result.stdout.str()


def test_dont_list_fixture_used_after_test_which_does_not_use_fixtures(testdir, message_template):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def same_file_fixture():
            return 1

        def test_no_fixture_used():
            assert True

        def test_simple(same_file_fixture):
            assert 1 == same_file_fixture
    """)

    result = testdir.runpytest('--dead-fixtures')
    message = message_template.format(
        'same_file_fixture',
        'test_dont_list_fixture_used_after_test_which_does_not_use_fixtures'
    )

    assert message not in result.stdout.str()


def test_doctest_should_not_result_in_false_positive(testdir, message_template):
    testdir.makepyfile("""
        import pytest


        @pytest.fixture()
        def same_file_fixture():
            return 1

        def something():
            ''' a doctest in a docstring
            >>> something()
            42
            '''
            return 42

        def test_simple(same_file_fixture):
            assert 1 == same_file_fixture
    """)

    result = testdir.runpytest('--dead-fixtures', '--doctest-modules')
    message = message_template.format(
        'same_file_fixture',
        'test_doctest_should_not_result_in_false_positive'
    )

    assert message not in result.stdout.str()
