import unittest

from nazk_renderer import render_declaration


class RendererTests(unittest.TestCase):
    def test_render_uses_proper_name_style(self):
        declaration = {
            "data": {
                "step_0": {"data": {"declaration_year": 2025}},
                "step_1": {
                    "data": {
                        "lastname": "ПІДКАПКА",
                        "firstname": "КОСТЯНТИН",
                        "middlename": "ВАСИЛЬОВИЧ",
                        "workPlace": "Тестова організація",
                        "workPost": "Посада",
                    }
                },
                "step_2": [],
                "step_3": [],
                "step_6": [],
                "step_8": [],
                "step_11": [],
                "step_12": [],
                "step_13": [],
            }
        }

        html = render_declaration(declaration)

        self.assertIn("Підкапка Костянтин Васильович", html)
        self.assertNotIn("ПІДКАПКА КОСТЯНТИН ВАСИЛЬОВИЧ", html)

    def test_render_skips_tabs_without_assets(self):
        declaration = {
            "data": {
                "step_0": {"data": {"declaration_year": 2025}},
                "step_1": {
                    "data": {
                        "lastname": "ПІДКАПКА",
                        "firstname": "КОСТЯНТИН",
                        "middlename": "ВАСИЛЬОВИЧ",
                        "workPlace": "Тестова організація",
                        "workPost": "Посада",
                    }
                },
                "step_2": [
                    {
                        "id": "2",
                        "lastname": "ПІДКАПКА",
                        "firstname": "ОЛЕНА",
                        "middlename": "АНАТОЛІЇВНА",
                        "subjectRelation": "дружина",
                    }
                ],
                "step_3": [],
                "step_6": [],
                "step_8": [],
                "step_11": [],
                "step_12": [],
                "step_13": [],
            }
        }

        html = render_declaration(declaration)

        self.assertIn("Підкапка Костянтин Васильович", html)
        self.assertNotIn("Підкапка Олена Анатоліївна", html)


if __name__ == "__main__":
    unittest.main()
