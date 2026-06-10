from heavyforge.codegov.config import KaskalConfig, load_config_file
from heavyforge.codegov.models import ReviewMode


def test_default_config_is_observe_mode():
    config = KaskalConfig()

    assert config.mode == ReviewMode.OBSERVE
    assert config.thresholds.full_review_max_changed_lines == 800
    assert config.policies.secrets_exposure is True


def test_load_config_file_overrides_values(tmp_path):
    path = tmp_path / ".kaskal.yml"
    path.write_text(
        """
mode: enforce
thresholds:
  full_review_max_changed_lines: 10
  warn_max_changed_lines: 20
policies:
  dependency_risk: false
""".strip(),
        encoding="utf-8",
    )

    config = load_config_file(path)

    assert config.mode == ReviewMode.ENFORCE
    assert config.thresholds.full_review_max_changed_lines == 10
    assert config.thresholds.warn_max_changed_lines == 20
    assert config.policies.dependency_risk is False
