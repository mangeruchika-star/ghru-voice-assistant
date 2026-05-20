"""Static college data and localized prompt text."""

from __future__ import annotations

COLLEGE_INFO = {
    "name": "G H Raisoni University Saikheda",
    "location": "Dhoda Borgaon, Saikheda, Tahsil Sausar, District Pandhurna",
    "email": "info@ghrus.edu.in",
    "website": "https://www.ghrus.edu.in",
    "office_timing": "10:00 AM to 5:00 PM, Monday to Saturday",
    "library_timing": "10:15 AM to 4:45 PM, Monday to Saturday",
    "courses": {
        "engineering": {
            "btech": [
                "Computer Science",
                "Mechanical Engineering",
                "Electrical Engineering",
                "Civil Engineering",
                "Electronics and Telecommunication",
                "Information Technology",
            ],
            "btech_fees": "INR 1,60,000 per year",
            "mtech": [
                "Computer Science",
                "VLSI Design",
                "Power Systems",
                "Structural Engineering",
            ],
            "mtech_fees": "INR 1,50,000 per year",
        },
        "science": {
            "bsc": [
                "Physics",
                "Chemistry",
                "Mathematics",
                "Computer Science",
                "Biology",
            ],
            "fees": "INR 50,000 per year",
            "msc": ["Physics", "Chemistry", "Mathematics", "Organic Chemistry"],
            "fees_postgraduate": "INR 80,000 per year",
            "computer_applications": {
                "bca": "INR 55,000 per year",
                "mca": "INR 80,000 per year",
            },
        },
        "diploma": {
            "courses": [
                "Computer Engineering",
                "Mechanical Engineering",
                "Civil Engineering",
                "Electrical Engineering",
                "Electronics Engineering",
            ],
            "fees": "INR 75,000 per year",
        },
    },
    "admission": {
        "process": "Online application, entrance exam, counseling, and fee payment",
        "entrance_exam": "G H R U S Common Entrance Test",
        "eligibility": "Minimum 50 percent marks in class 12 for undergraduate courses",
    },
    "fees": {
        "engineering": "INR 1,50,000 per year",
        "btech": "INR 1,60,000 per year",
        "mtech": "INR 1,50,000 per year",
        "science": "INR 50,000 per year",
        "bca": "INR 55,000 per year",
        "mca": "INR 80,000 per year",
        "commerce": "INR 1,00,000 per year",
        "diploma": "INR 75,000 per year",
        "hostel": "INR 95,000 per year with mess",
        "transport": "INR 30,000 to INR 40,000 per year depending on distance",
    },
    "facilities": {
        "library": "Well-stocked library with academic and reference books",
        "laboratories": [
            "Computer Lab",
            "Physics Lab",
            "Chemistry Lab",
            "Mechanical Workshop",
            "Electrical Lab",
            "Language Lab",
        ],
        "sports": [
            "Cricket Ground",
            "Football Field",
            "Basketball Court",
            "Tennis Court",
            "Volleyball Court",
            "Swimming Pool",
            "Gymnasium",
            "Indoor Stadium",
        ],
        "hostel": "Separate hostels for boys and girls with Wi-Fi, mess, laundry, and recreation room",
        "transport": "Bus facility available on multiple routes",
        "medical": "Doctor support, 24 by 7 medical room, and ambulance on call",
        "wifi": "Campus-wide high-speed Wi-Fi is available in academic blocks, library, labs, and hostel areas for students and staff",
    },
    "exams": {
        "internal": "Internal exams are generally conducted within 45 days of the semester start",
        "external": "University exams are usually held in November to December and April to May",
        "result": "Results are normally declared within 30 to 60 days of the exam",
        "revaluation": "Revaluation can be applied for within 15 to 20 days after results",
    },
    "departments": {
        "admission": "admission@ghrus.edu.in",
        "examination": "exam@ghrus.edu.in",
        "library": "library@ghrus.edu.in",
        "hostel": "hostel@ghrus.edu.in",
    },
}

COLLEGE_INFO_HI = {
    "name": "जी एच रायसोनी यूनिवर्सिटी साईंखेड़ा",
    "नाम": "जी एच रायसोनी यूनिवर्सिटी साईंखेड़ा",
    "location": "ढोडा बोरगांव, साईंखेड़ा, तहसील सौंसर, जिला पांढुर्ना",
    "लोकेशन": "ढोडा बोरगांव, साईंखेड़ा, तहसील सौंसर, जिला पांढुर्ना",
    "email": "info@ghrus.edu.in",
    "website": "https://www.ghrus.edu.in",
    "office_timing": "सुबह 10:00 से शाम 5:00, सोमवार से शनिवार",
    "library_timing": "सुबह 10:15 से शाम 4:45, सोमवार से शनिवार",
    "courses": {
        "engineering": {
            "btech": [
                "कंप्यूटर साइंस",
                "मैकेनिकल इंजीनियरिंग",
                "इलेक्ट्रिकल इंजीनियरिंग",
                "सिविल इंजीनियरिंग",
                "इलेक्ट्रॉनिक्स एंड टेलीकम्युनिकेशन",
                "इन्फॉर्मेशन टेक्नोलॉजी",
            ],
            "btech_fees": "INR 1,60,000 प्रति वर्ष",
            "mtech": [
                "कंप्यूटर साइंस",
                "वीएलएसआई डिजाइन",
                "पावर सिस्टम्स",
                "स्ट्रक्चरल इंजीनियरिंग",
            ],
            "mtech_fees": "INR 1,50,000 प्रति वर्ष",
        },
        "science": {
            "bsc": [
                "फिजिक्स",
                "केमिस्ट्री",
                "मैथमेटिक्स",
                "कंप्यूटर साइंस",
                "बायोलॉजी",
            ],
            "bsc_fees": "INR 50,000 प्रति वर्ष",
            "msc": ["फिजिक्स", "केमिस्ट्री", "मैथमेटिक्स", "ऑर्गेनिक केमिस्ट्री"],
            "fees": "INR 50,000 प्रति वर्ष",
            "fees_postgraduate": "INR 80,000 प्रति वर्ष",
            "computer_applications": {
                "bca": "INR 55,000 प्रति वर्ष",
                "mca": "INR 80,000 प्रति वर्ष",
            },
        },
        "diploma": {
            "courses": [
                "कंप्यूटर इंजीनियरिंग",
                "मैकेनिकल इंजीनियरिंग",
                "सिविल इंजीनियरिंग",
                "इलेक्ट्रिकल इंजीनियरिंग",
                "इलेक्ट्रॉनिक्स इंजीनियरिंग",
            ],
            "fees": "INR 75,000 प्रति वर्ष",
        },
    },
    "admission": {
        "process": "ऑनलाइन एप्लिकेशन, एंट्रेंस एग्जाम, काउंसलिंग और फीस पेमेंट",
        "entrance_exam": "जी एच आर यू एस कॉमन एंट्रेंस टेस्ट",
        "eligibility": "अंडरग्रेजुएट कोर्स के लिए 12वीं में कम से कम 50 प्रतिशत अंक",
    },
    "fees": {
        "engineering": "INR 1,50,000 प्रति वर्ष",
        "btech": "INR 1,60,000 प्रति वर्ष",
        "mtech": "INR 1,50,000 प्रति वर्ष",
        "science": "INR 50,000 प्रति वर्ष",
        "bca": "INR 55,000 प्रति वर्ष",
        "mca": "INR 80,000 प्रति वर्ष",
        "commerce": "INR 1,00,000 प्रति वर्ष",
        "diploma": "INR 75,000 प्रति वर्ष",
        "hostel": "INR 95,000 प्रति वर्ष (मेस सहित)",
        "transport": "INR 30,000 से INR 40,000 प्रति वर्ष (दूरी के अनुसार)",
    },
    "facilities": {
        "library": "अच्छी तरह से सुसज्जित लाइब्रेरी, जिसमें अकादमिक और रेफरेंस बुक्स उपलब्ध हैं",
        "laboratories": [
            "कंप्यूटर लैब",
            "फिजिक्स लैब",
            "केमिस्ट्री लैब",
            "मैकेनिकल वर्कशॉप",
            "इलेक्ट्रिकल लैब",
            "लैंग्वेज लैब",
        ],
        "sports": [
            "क्रिकेट ग्राउंड",
            "फुटबॉल फील्ड",
            "बास्केटबॉल कोर्ट",
            "टेनिस कोर्ट",
            "वॉलीबॉल कोर्ट",
            "स्विमिंग पूल",
            "जिमनैजियम",
            "इंडोर स्टेडियम",
        ],
        "hostel": "लड़कों और लड़कियों के लिए अलग हॉस्टल, वाई-फाई, मेस, लॉन्ड्री और रिक्रिएशन रूम के साथ",
        "transport": "कई रूट्स पर बस सुविधा उपलब्ध है",
        "medical": "डॉक्टर सपोर्ट, 24x7 मेडिकल रूम और जरूरत पड़ने पर एम्बुलेंस उपलब्ध",
        "wifi": "पूरे कैंपस में हाई-स्पीड वाई-फाई उपलब्ध है, जिसमें अकादमिक ब्लॉक, लाइब्रेरी, लैब और हॉस्टल क्षेत्र शामिल हैं",
    },
    "exams": {
        "internal": "इंटरनल एग्जाम आमतौर पर सेमेस्टर शुरू होने के 45 दिनों के अंदर होते हैं",
        "external": "यूनिवर्सिटी एग्जाम आमतौर पर नवंबर-दिसंबर और अप्रैल-मई में होते हैं",
        "result": "एग्जाम के 30 से 60 दिनों के अंदर रिजल्ट जारी होता है",
        "revaluation": "रिजल्ट के बाद 15 से 20 दिनों के अंदर रीवैल्यूएशन के लिए आवेदन किया जा सकता है",
    },
    "departments": {
        "admission": "admission@ghrus.edu.in",
        "examination": "exam@ghrus.edu.in",
        "library": "library@ghrus.edu.in",
        "hostel": "hostel@ghrus.edu.in",
    },
}

RESPONSES = {
    "en": {
        "assistant_name": "GHRU Voice Assistant",
        "welcome": "Welcome to the G H Raisoni University Saikheda voice assistant.",
        "language_selected": "English language selected.",
        "help": (
            "You can ask about courses, fees, admission, facilities, exam schedule, "
            "departments, office timings, contact details, current time, or say exit."
        ),
        "prompt": "What next you want to know?",
        "not_understood": "I could not understand that. Please try again.",
        "goodbye": "Thank you for using the voice assistant. Goodbye.",
        "input_fallback": "Microphone input is unavailable, so I will use keyboard input.",
        "recognition_unavailable": (
            "Your microphone is working, but speech recognition service is unavailable right now. "
            "Please try again or type your question."
        ),
    },
    "hi": {
        "assistant_name": "जी एच आर यू वॉइस असिस्टेंट",
        "welcome": "जीएच रायसोनी यूनिवर्सिटी साईंखेड़ा वॉइस असिस्टेंट में आपका स्वागत है।",
        "language_selected": "हिंदी भाषा चुनी गई है।",
        "help": (
            "आप कोर्स, फीस, एडमिशन, सुविधाएं, परीक्षा, विभाग, टाइमिंग, संपर्क जानकारी, "
            "वर्तमान समय पूछ सकते हैं या एग्जिट बोल सकते हैं।"
        ),
        "prompt": "मैं आपकी कैसे मदद कर सकता हूँ?",
        "not_understood": "मैं समझ नहीं पाया। कृपया फिर से कोशिश करें।",
        "goodbye": "वॉइस असिस्टेंट का उपयोग करने के लिए धन्यवाद।",
        "input_fallback": "माइक्रोफोन इनपुट उपलब्ध नहीं है, इसलिए मैं टेक्स्ट इनपुट उपयोग करूँगा।",
        "recognition_unavailable": (
            "आपका माइक्रोफोन काम कर रहा है, लेकिन स्पीच रिकग्निशन सेवा अभी उपलब्ध नहीं है। "
            "कृपया दोबारा कोशिश करें या अपना प्रश्न टाइप करें।"
        ),
    },
}
