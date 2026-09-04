import unittest

from app.weather import extract_weather_location, is_weather_question


class WeatherTests(unittest.TestCase):
    def test_weather_detection(self):
        self.assertTrue(is_weather_question("weather tomorrow in Amman"))
        self.assertTrue(is_weather_question("كيف الطقس في عمان؟"))
        self.assertFalse(is_weather_question("write Python code"))

    def test_location_extraction(self):
        self.assertEqual(extract_weather_location("weather tomorrow in Amman"), "Amman")
        self.assertEqual(extract_weather_location("what is the weather in Amman, Jordan tomorrow?"), "Amman, Jordan")
        self.assertEqual(extract_weather_location("كيف الطقس في عمان غدا؟"), "عمان")


if __name__ == "__main__":
    unittest.main()
