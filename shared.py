this_is_shared = "test of shared global"
extra_cmd_prompts = {}
noise  = "https://duy7y3nglgmh.cloudfront.net/FootballCrowdSound.mp3"
noise2 = "https://duy7y3nglgmh.cloudfront.net/SoccerStadiumSoundEffect.mp3"
noise3 = "https://duy7y3nglgmh.cloudfront.net/SportsStadiumCrowdCheering.mp3"
noise_max_millis = 4 * 60 * 1000
noise2_max_millis = 40 * 1000
noise3_max_millis = 40 * 1000
doc = "doc://alexa/apla/documents/unchanged_template_from_tools"

datasources2 = {

    "gridListData": {
        "type": "object",
        "objectId": "gridListSample",
        "backgroundImage": {
            "contentDescription": "this is the content",
            "smallSourceUrl": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
            "largeSourceUrl": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
            "sources": [
                {
                    "url": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
                    "size": "small",
                    "widthPixels": 0,
                    "heightPixels": 0
                },
                {
                    "url": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
                    "size": "large",
                    "widthPixels": 0,
                    "heightPixels": 0
                }
            ]
        },
        "title": "You can ask about ....",
        "listItems": [
            {
                "primaryText": "The Table",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/thetable.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["table"]}]
            },
            {
                "primaryText": "Fixtures",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/fixtures.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["fixtures"]}]
            },
            {
                "primaryText": "Results",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/results.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["results"]}]
            },
            {
                "primaryText": "Teams",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/teams.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["teams"]}]
            },
            {
                "primaryText": "Points By Week",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/linechart.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["line"]}]
            },
            {
                "primaryText": "Relegation",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/relegation.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["relegation"]}]
            },
            {
                "primaryText": "Clean Sheets",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_keeper.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["cleansheet"]}]
            },
            {
                "primaryText": "Fouls",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/fouls.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["fouls"]}]
            },
            {
                "primaryText": "Goals",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_goal.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["goals"]}]
            },
            {
                "primaryText": "Goal Difference",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/GoalDifference.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["goaldifference"]}]
            },
            {
                "primaryText": "Keeper Saves vs Goals",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/savepercent.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["savepercent"]}]
            },
            {
                "primaryText": "Goals vs Shots",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/goals_shots.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["goals_shots"]}]
            },
            {
                "primaryText": "Red Card",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/redcard.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["redcard"]}]
            },
            {
                "primaryText": "Referees",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_referee.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["referee"]}]
            },
            {
                "primaryText": "Tackles",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/tackles.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["tackles"]}]
            },
            {
                "primaryText": "Touches",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_touches.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["touches"]}]
            },
            {
                "primaryText": "Yellow Card",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/yellowcard.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["yellowcard"]}]
            },
            {
                "primaryText": "Leave a Review",
                "imageScale": "best-fit",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/qr_code.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Leave a Review"]}]
            },
        ],
    }                        
} 

datasourcessp = {

    "gridListData": {
        "type": "object",
        "objectId": "gridListSample",
        "backgroundImage": {
            "contentDescription": "this is the content",
            "smallSourceUrl": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
            "largeSourceUrl": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
            "sources": [
                {
                    "url": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
                    "size": "small",
                    "widthPixels": 0,
                    "heightPixels": 0
                },
                {
                    "url": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
                    "size": "large",
                    "widthPixels": 0,
                    "heightPixels": 0
                }
            ]
        },
        "title": "Puedes preguntar sobre ....",
        "listItems": [
            {
                "primaryText": "La mesa",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/thetable.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["table"]}]
            },
            {
                "primaryText": "los fósforos",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/fixtures.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["fixtures"]}]
            },
            {
                "primaryText": "Resultados",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/results.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["results"]}]
            },
            {
                "primaryText": "Equipos",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/teams.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["teams"]}]
            },
            {
                "primaryText": "Puntos por semana",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/linechart.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["line"]}]
            },
            {
                "primaryText": "Descenso",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/relegation.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["relegation"]}]
            },
            {
                "primaryText": "Sábanas limpias",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_keeper.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["cleansheet"]}]
            },
            {
                "primaryText": "Faltas",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/fouls.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["fouls"]}]
            },
            {
                "primaryText": "Metas",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_goal.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["goals"]}]
            },
            {
                "primaryText": "Diferencia de goles",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/GoalDifference.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["goaldifference"]}]
            },
            {
                "primaryText": "El portero salva vs. Goles",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/savepercent.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["savepercent"]}]
            },
            {
                "primaryText": "La tarjeta roja",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/redcard.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["redcard"]}]
            },
            {
                "primaryText": "Arbitrar",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_referee.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["referee"]}]
            },
            {
                "primaryText": "Taclear",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/tackles.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["tackles"]}]
            },
            {
                "primaryText": "Toca",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Depositphotos_touches.jpg",
                "primaryAction": [{"type": "SendEvent","arguments": ["touches"]}]
            },
            {
                "primaryText": "la tarjeta amarilla",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/yellowcard.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["yellowcard"]}]
            },
            {
                "primaryText": "Dejar un comentario",
                "imageScale": "best-fit",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/qr_code.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Leave a Review"]}]
            },
        ],
    }                        
} 

test_speach_data =  {
    "referee" : "The most used referees are Martin Atkinson with 22 yellow cards and 4 red cards, \
                              Anthony Taylor with 3 yellow cards and 17 red cards",
    "touches" : "The players with the most touches were Kane with all of them, Son with some of them, and Vardy with the rest of them ",
    "tackles" : "Various players had various number of tackles, some fair and some not so fair",
    "fouls"   : "While you can argue about players diving there are certainly times when real fouls happen"
}

noise_data = [
    ("https://duy7y3nglgmh.cloudfront.net/FootballCrowdSound.mp3", 4 * 60 * 1000),
    ("https://duy7y3nglgmh.cloudfront.net/SoccerStadiumSoundEffect.mp3", 40 * 1000),
    ("https://duy7y3nglgmh.cloudfront.net/SportsStadiumCrowdCheering.mp3", 40 * 1000)
]

teamsdatasource = {
    "radioButtonExampleData": {
        "radioButtonGroupItems": [
            {
                "radioButtonId": "Form",
                "radioButtonText": "ShowTeamForm",
                "radioButtonHeight": "15px",
                "radioButtonChecked": "True",
                "disabled": "True"
            },
            {
                "radioButtonId": "Results",
                "radioButtonText": "ShowTeamResults",
                "radioButtonHeight": "15px",
                "radioButtonChecked": "False",
                "disabled": "True"
            },
            {
                "radioButtonId": "Fixtures",
                "radioButtonText": "ShowTeamFixtures",
                "radioButtonHeight": "15px",
                "disabled": "True",
                "radioButtonChecked": "False"
            }
        ]
    },
    "gridListData": {
        "type": "object",
        "objectId": "gridListSample",
        "backgroundImage": {
            "contentDescription": "this is the content",
            "smallSourceUrl": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
            "largeSourceUrl": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
            "sources": [
                {
                    "url": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
                    "size": "small",
                    "widthPixels": 0,
                    "heightPixels": 0
                },
                {
                    "url": "https://duy7y3nglgmh.cloudfront.net/football_pitch.png",
                    "size": "large",
                    "widthPixels": 0,
                    "heightPixels": 0
                }
            ]
        },
        "title": "You can ask about each team",
        "listItems": [
            {
                "primaryText": "Arsenal",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Arsenal.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Arsenal", "${CurrentSelectedRadioButtonId}"]}]
            },
            {
                "primaryText": "Aston Villa",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/AstonVilla.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Aston Villa"]}]
            },
            {
                "primaryText": "Brentford",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Brentford.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Brentford"]}]
            },
            {
                "primaryText": "Brighton",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/BrightonAndHoveAlbion.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Brighton and Hove Albion"]}]
            },
            {
                "primaryText": "Burnley",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Burnley.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Burnley"]}]
            },
            {
                "primaryText": "Chelsea",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Chelsea.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Chelsea"]}]
            },
            {
                "primaryText": "Crystal Palace",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/CrystalPalace.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Crystal Palace"]}]
            },
            {
                "primaryText": "Everton",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Everton.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Everton"]}]
            },
            {
                "primaryText": "Leeds United",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/LeedsUnited.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Leeds United"]}]
            },
            {
                "primaryText": "Leicester City",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/LeicesterCity.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Leicester City"]}]
            },
            {
                "primaryText": "Liverpool",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Liverpool.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Liverpool"]}]
            },
            {
                "primaryText": "Manchester City",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/ManchesterCity.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Manchester City"]}]
            },
            {
                "primaryText": "Manchester United",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/ManchesterUnited.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Manchester United"]}]
            },
            {
                "primaryText": "NewcastleUnited",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/NewcastleUnited.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Newcastle United"]}]
            },
            {
                "primaryText": "Norwich City",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/NorwichCity.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Norwich City"]}]
            },
            {
                "primaryText": "Southampton",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Southampton.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Southampton"]}]
            },
            {
                "primaryText": "Tottenham Hotspur",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/TottenhamHotspur.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Tottenham Hotspur"]}]
            },
            {
                "primaryText": "Watford",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/Watford.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Watford"]}]
            },
            {
                "primaryText": "Westham United",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/WestHamUnited.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Westham United"]}]
            },
            {
                "primaryText": "Wolverhampton Wanderers",
                "imageSource": "https://duy7y3nglgmh.cloudfront.net/WolverhamptonWanderers.png",
                "primaryAction": [{"type": "SendEvent","arguments": ["Wolverhampton Wanderers"]}]
            },
            {
                "primaryText": " ",
                "primaryAction": [{"type": "Idle","arguments": [""]}]
            },
            {
                "primaryText": " ",
                "primaryAction": [{"type": "Idle","arguments": [""]}]
            }
        ],
        "logoUrl": "https://duy7y3nglgmh.cloudfront.net/redcard.png"
    }                        
}
