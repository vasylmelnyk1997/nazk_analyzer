import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from parser import map_document
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


    def test_income_person_who_care_via_parser(self):
        """map_document повинен витягувати доходи з person_who_care (реальний формат API)."""
        raw = {
            "id": "x", "user_declarant_id": 1, "declaration_year": 2024,
            "data": {
                "step_1": {"data": {"lastname": "ТЕСТ", "firstname": "А", "middlename": "",
                                    "workPlace": "", "workPost": ""}},
                "step_2": {"data": []},
                "step_3": {"data": []}, "step_6": {"data": []}, "step_8": {"data": []},
                "step_11": {"data": [
                    {"objectType": "Заробітна плата", "sizeIncome": "113392",
                     "person_who_care": [{"person": "1"}]},
                ]},
                "step_12": {"data": []}, "step_13": {"data": []},
            },
        }
        mapped = map_document(raw)
        s11 = mapped["data"]["step_11"]["data"]
        self.assertEqual(len(s11), 1)
        self.assertEqual(s11[0]["rights"], [{"rightBelongs": "1", "percentOwnership": None}])
        html = render_all_declarations([mapped])
        self.assertIn("Заробітна плата", html)
        self.assertIn("113 392 грн", html)

    def test_general_realty_shows_owner(self):
        """Вкладка 'Загальна': рядок нерухомості містить ім'я власника."""
        step_3 = [{
            "objectType": "Квартира", "totalArea": "50",
            "region": "м. Київ", "region_txt": "", "district": "", "district_txt": "",
            "city": "Київ", "city_txt": "", "cityType": "Місто", "owningDate": "2020-01-01",
            "rights": [{"rightBelongs": "1", "percentOwnership": None}],
        }]
        doc = _make_doc()
        doc["data"]["step_3"]["data"] = step_3
        html = render_all_declarations([doc])
        self.assertIn("власник: Підкапка Костянтин Васильович", html)

    def test_general_vehicle_shows_owners(self):
        """Вкладка 'Загальна': рядок ТЗ із двома власниками містить 'власники: ...'"""
        step_2 = [{
            "id": "2", "lastname": "ПІДКАПКА", "firstname": "ОЛЕНА",
            "middlename": "АНАТОЛІЇВНА", "subjectRelation": "дружина",
        }]
        step_6 = [{
            "objectType": "Легковий автомобіль", "brand": "Toyota", "model": "Camry",
            "graduationYear": "2020", "owningDate": "2021-05-01",
            "rights": [
                {"rightBelongs": "1", "percentOwnership": None},
                {"rightBelongs": "2", "percentOwnership": None},
            ],
        }]
        doc = _make_doc(step_2=step_2)
        doc["data"]["step_6"]["data"] = step_6
        html = render_all_declarations([doc])
        self.assertIn("власники:", html)
        self.assertIn("Підкапка Костянтин Васильович", html)
        self.assertIn("Підкапка Олена Анатоліївна", html)


if __name__ == "__main__":
    unittest.main()
