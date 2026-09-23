"""Tests for RPM weak-dependency spec headers.

Covers the Recommends/Supplements/Suggests/Enhances headers (rpm 4.12+),
driven by the X_RPM_* environment variables and rendered through
rpm_val.generate_values(). Each accepts either a scalar or a list, matching
the existing Requires/Provides/Conflicts/Obsoletes behavior.
"""
import pytest

import parts.pieces.rpm_val as rpm_val
import parts.settings as parts_settings


WEAK_DEPS = [
    ('Recommends', 'X_RPM_RECOMMENDS'),
    ('Supplements', 'X_RPM_SUPPLEMENTS'),
    ('Suggests', 'X_RPM_SUGGESTS'),
    ('Enhances', 'X_RPM_ENHANCES'),
]

# Render only the weak-dep headers so the test doesn't drag in the required
# fields (Name/Version/...) and their error path.
WEAK_DEP_HEADERS = [h for h in rpm_val.headers if h['key'] in {k for k, _ in WEAK_DEPS}]


@pytest.fixture
def env():
    return parts_settings.DefaultSettings().Environment()


def _spec_for(env, **rpm_vars):
    for k, v in rpm_vars.items():
        env[k] = v
    return rpm_val.generate_values(WEAK_DEP_HEADERS, env)


class TestWeakDependencyHeaders:
    def test_each_weak_dep_is_a_registered_header(self):
        keys = {item['key'] for item in rpm_val.headers}
        for header_key, _ in WEAK_DEPS:
            assert header_key in keys

    @pytest.mark.parametrize('header_key,var', WEAK_DEPS)
    def test_scalar_value_renders(self, env, header_key, var):
        out = _spec_for(env, **{var: 'somepkg'})
        assert '{0}: somepkg\n'.format(header_key) in out

    @pytest.mark.parametrize('header_key,var', WEAK_DEPS)
    def test_list_value_is_comma_joined(self, env, header_key, var):
        out = _spec_for(env, **{var: ['pkga', 'pkgb']})
        assert '{0}: pkga,pkgb\n'.format(header_key) in out

    @pytest.mark.parametrize('header_key,var', WEAK_DEPS)
    def test_absent_value_is_not_emitted(self, env, header_key, var):
        out = rpm_val.generate_values(WEAK_DEP_HEADERS, env)
        assert header_key not in out

    def test_weak_deps_render_independently(self, env):
        out = _spec_for(
            env,
            X_RPM_RECOMMENDS=['a', 'b'],
            X_RPM_SUPPLEMENTS='c',
            X_RPM_SUGGESTS=['d'],
            X_RPM_ENHANCES='e',
        )
        assert 'Recommends: a,b\n' in out
        assert 'Supplements: c\n' in out
        assert 'Suggests: d\n' in out
        assert 'Enhances: e\n' in out
