"""Static crop reference data.

Each entry is a 4-tuple:
    (image_path, growing_regions, season, export_destinations)
"""

CROP_DATA = {
    "wheat": [
        "/static/images/wheat.jpg",
        "Uttar Pradesh, Punjab, Haryana, Rajasthan, Madhya Pradesh, Bihar",
        "rabi",
        "Sri Lanka, United Arab Emirates, Taiwan",
    ],
    "paddy": [
        "/static/images/paddy.jpg",
        "West Bengal, Uttar Pradesh, Andhra Pradesh, Punjab, Tamil Nadu",
        "kharif",
        "Bangladesh, Saudi Arabia, Iran",
    ],
    "barley": [
        "/static/images/barley.jpg",
        "Rajasthan, Uttar Pradesh, Madhya Pradesh, Haryana, Punjab",
        "rabi",
        "Oman, United Kingdom, Qatar, USA",
    ],
    "maize": [
        "/static/images/maize.jpg",
        "Karnataka, Andhra Pradesh, Tamil Nadu, Rajasthan, Maharashtra",
        "kharif",
        "Hong Kong, United Arab Emirates, France",
    ],
    "bajra": [
        "/static/images/bajra.jpg",
        "Rajasthan, Maharashtra, Haryana, Uttar Pradesh, Gujarat",
        "kharif",
        "Oman, Saudi Arabia, Israel, Japan",
    ],
    "copra": [
        "/static/images/copra.jpg",
        "Kerala, Tamil Nadu, Karnataka, Andhra Pradesh, Odisha, West Bengal",
        "rabi",
        "Vietnam, Bangladesh, Iran, Malaysia",
    ],
    "cotton": [
        "/static/images/cotton.jpg",
        "Punjab, Haryana, Maharashtra, Tamil Nadu, Madhya Pradesh, Gujarat",
        "kharif",
        "China, Bangladesh, Egypt",
    ],
    "masoor": [
        "/static/images/masoor.jpg",
        "Uttar Pradesh, Madhya Pradesh, Bihar, West Bengal, Rajasthan",
        "rabi",
        "Pakistan, Cyprus, United Arab Emirates",
    ],
    "gram": [
        "/static/images/gram.jpg",
        "Madhya Pradesh, Maharashtra, Rajasthan, Uttar Pradesh, Andhra Pradesh, Karnataka",
        "rabi",
        "Vietnam, Spain, Myanmar",
    ],
    "groundnut": [
        "/static/images/groundnut.jpg",
        "Andhra Pradesh, Gujarat, Tamil Nadu, Karnataka, Maharashtra",
        "kharif",
        "Indonesia, Jordan, Iraq",
    ],
    "arhar": [
        "/static/images/arhar.jpg",
        "Maharashtra, Karnataka, Uttar Pradesh, Madhya Pradesh",
        "kharif",
        "United Arab Emirates, USA, Chicago",
    ],
    "sesamum": [
        "/static/images/sesamum.jpg",
        "Maharashtra, Rajasthan, West Bengal, Andhra Pradesh, Gujarat",
        "rabi",
        "Iraq, South Africa, USA, Netherlands",
    ],
    "jowar": [
        "/static/images/jowar.jpg",
        "Maharashtra, Karnataka, Rajasthan, Madhya Pradesh, Gujarat",
        "kharif",
        "Toronto, Sydney, New York",
    ],
    "moong": [
        "/static/images/moong.jpg",
        "Rajasthan, Maharashtra, Uttar Pradesh",
        "rabi",
        "Qatar, United States, Canada",
    ],
    "niger": [
        "/static/images/niger.jpg",
        "Andhra Pradesh, Assam, Chhattisgarh, Gujarat, Jharkhand",
        "kharif",
        "United States of America, Argentina, Belgium",
    ],
    "rape": [
        "/static/images/rape.jpg",
        "Rajasthan, Uttar Pradesh, Haryana, Madhya Pradesh, Gujarat",
        "rabi",
        "Vietnam, Malaysia, Taiwan",
    ],
    "jute": [
        "/static/images/jute.jpg",
        "West Bengal, Assam, Odisha, Bihar, Uttar Pradesh",
        "kharif",
        "Jordan, United Arab Emirates, Taiwan",
    ],
    "safflower": [
        "/static/images/safflower.jpg",
        "Maharashtra, Karnataka, Andhra Pradesh, Madhya Pradesh, Odisha",
        "rabi",
        "Philippines, Taiwan, Portugal",
    ],
    "soyabean": [
        "/static/images/soyabean.jpg",
        "Madhya Pradesh, Maharashtra, Rajasthan, Uttar Pradesh",
        "kharif",
        "Spain, Thailand, Singapore",
    ],
    "urad": [
        "/static/images/urad.jpg",
        "Andhra Pradesh, Maharashtra, Madhya Pradesh, Tamil Nadu",
        "rabi",
        "United States, Canada, United Arab Emirates",
    ],
    "ragi": [
        "/static/images/ragi.jpg",
        "Maharashtra, Karnataka, Tamil Nadu, Uttarakhand",
        "kharif",
        "United Arab Emirates, New Zealand, Bahrain",
    ],
    "sunflower": [
        "/static/images/sunflower.jpg",
        "Karnataka, Andhra Pradesh, Maharashtra, Bihar, Odisha",
        "rabi",
        "Philippines, United States, Bangladesh",
    ],
    "sugarcane": [
        "/static/images/sugarcane.jpg",
        "Uttar Pradesh, Maharashtra, Tamil Nadu, Karnataka, Andhra Pradesh",
        "kharif",
        "Kenya, United Arab Emirates, United Kingdom",
    ],
}


def crop(crop_name):
    """Return the 4-tuple of reference data for ``crop_name``."""
    key = (crop_name or "").strip().lower()
    if key not in CROP_DATA:
        raise KeyError(
            f"Unknown crop '{crop_name}'. Available: {', '.join(sorted(CROP_DATA))}"
        )
    return CROP_DATA[key]
