import unittest

from renderer import render_all_declarations


def _make_doc(step_11=None, step_2=None, step_12=None, year=2025):
    return {
        "id": "test-id",
        "user_declarant_id": 1,
        "declaration_year": year,
        "data": {
            "step_1": {
                "data": {
                    "lastname": "ПІДКАПКА",
                    "firstname": "КОСТЯНТИН",
                    "middlename": "ВАСИЛЬОВИЧ",
                    "workPlace": "Тестова організація",
                    "workPost": "Посада",
                }
            },
            "step_2": {"data": step_2 or []},
            "step_3": {"data": []},
            "step_6": {"data": []},
            "step_8": {"data": []},
            "step_11": {"data": step_11 or []},
            "step_12": {"data": step_12 or []},
            "step_13": {"data": []},
        },
    }


class RendererTests(unittest.TestCase):
    def test_render_uses_proper_name_style(self):
        html = render_all_declarations([_make_doc()])
        self.assertIn("Підкапка Костянтин Васильович", html)
        self.assertNotIn("ПІДКАПКА КОСТЯНТИН ВАСИЛЬОВИЧ", html)

    def test_render_skips_owner_tabs_without_assets(self):
        step_2 = [
            {
                "id": "2",
                "lastname": "ПІДКАПКА",
                "firstname": "ОЛЕНА",
                "middlename": "АНАТОЛІЇВНА",
                "subjectRelation": "дружина",
            }
        ]
        html = render_all_declarations([_make_doc(step_2=step_2)])
        self.assertIn("Підкапка Костянтин Васильович", html)
        # дружина без активів: присутня в таблиці "Склад сім'ї", але немає owner-btn вкладки
        self.assertIn("Підкапка Олена Анатоліївна", html)          # є в склад сім'ї
        self.assertNotRegex(html, r'owner-btn[^>]*>Підкапка Олена')  # але не як вкладка

    def test_render_income_with_rights(self):
        step_11 = [
            {
                "objectType": "Заробітна плата",
                "sizeIncome": 100,
                "rights": [{"rightBelongs": "1", "percentOwnership": "100"}],
            }
        ]
        html = render_all_declarations([_make_doc(step_11=step_11)])
        # доходи відображаються через _expandable -> <table>, не <li>
        self.assertIn("Заробітна плата", html)
        self.assertNotRegex(html, r"<li>\d+\. ")
        self.assertIn('class="summary-toggle"', html)

    def test_general_tab_always_present(self):
        html = render_all_declarations([_make_doc()])
        self.assertIn("Загальна", html)

    def test_savings_computed_across_years(self):
        # рік 1: 100 000 UAH, рік 2: 150 000 UAH → заощадження = 50 000
        s12_y1 = [{"objectType": "Готівкові кошти", "sizeAssets": "100000",
                   "assetsCurrency": "UAH",
                   "rights": [{"rightBelongs": "1", "percentOwnership": "100"}]}]
        s12_y2 = [{"objectType": "Готівкові кошти", "sizeAssets": "150000",
                   "assetsCurrency": "UAH",
                   "rights": [{"rightBelongs": "1", "percentOwnership": "100"}]}]
        docs = [_make_doc(step_12=s12_y1, year=2023), _make_doc(step_12=s12_y2, year=2024)]
        html = render_all_declarations(docs)
        self.assertIn("50 000 грн", html)


if __name__ == "__main__":
    unittest.main()
