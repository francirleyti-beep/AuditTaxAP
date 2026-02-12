import unittest
import os
from unittest.mock import patch
from decimal import Decimal
from src.utils.config import Config

class TestConfig(unittest.TestCase):
    
    @patch.dict(os.environ, {
        "SEFAZ_URL": "http://test.com",
        "SEFAZ_TIMEOUT": "60",
        "HEADLESS_MODE": "True",
        "AUDIT_TOLERANCE": "0.10",
        "LOG_LEVEL": "DEBUG"
    })
    def test_load_from_env(self):
        # Force reload or just access Config properties if they are dynamic or re-read
        # Since Config properties are class attributes initialized at import time, 
        # patching os.environ MIGHT NOT work if Config is already imported and initialized.
        # However, for this test, let's try to reload the module or just trust logic if we designed it to be dynamic.
        # The current Config design reads os.getenv at class level (import time).
        # So we need to reload it.
        
        import importlib
        import src.utils.config
        importlib.reload(src.utils.config)
        from src.utils.config import Config as ReloadedConfig
        
        self.assertEqual(ReloadedConfig.SEFAZ_URL, "http://test.com")
        self.assertEqual(ReloadedConfig.SEFAZ_TIMEOUT, 60)
        self.assertTrue(ReloadedConfig.is_headless())
        self.assertEqual(ReloadedConfig.get_audit_tolerance(), Decimal("0.10"))
        self.assertEqual(ReloadedConfig.LOG_LEVEL, "DEBUG")

    def test_defaults(self):
        # Unset env vars to test defaults
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import src.utils.config
            importlib.reload(src.utils.config)
            from src.utils.config import Config as DefaultsConfig
            
            self.assertEqual(DefaultsConfig.SEFAZ_URL, "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php")
            self.assertFalse(DefaultsConfig.is_headless())
            self.assertEqual(DefaultsConfig.get_audit_tolerance(), Decimal("0.05"))

if __name__ == "__main__":
    unittest.main()
