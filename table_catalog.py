TABLE_CATALOG = {

    "circuits": {
        "description": """
Stores information about Formula 1 racing circuits.

Contains the circuit name, country, location and geographic coordinates.
""",

        "keywords": [
            "circuit",
            "track",
            "race location",
            "country",
            "latitude",
            "longitude",
            "Monaco circuit",
            "Silverstone",
            "Monza",
            "Bahrain",
            "Spa"
        ],

        "important_columns": [
            "circuitId",
            "name",
            "location",
            "country",
            "lat",
            "lng"
        ]
    },


    "races": {
        "description": """
Stores Formula 1 race information.

Contains race name, season year, round number, race date, race time and the circuit where the race was held.
""",

        "keywords": [
            "race",
            "Grand Prix",
            "season",
            "year",
            "race date",
            "race time",
            "Monaco Grand Prix",
            "Bahrain Grand Prix",
            'circuit',
            'grand prix',
            'calendar',
            'event'
        ],

        "important_columns": [
            "raceId",
            "year",
            "round",
            "circuitId",
            "name",
            "date",
            "time"
        ]
    },
    

    "results":{
        "description": """
Stores the finishing results of every driver in every Formula 1 race.
Contains finishing position, points, laps, finish time, fastest lap, fastest lap speed and race status.
This is the central table that connects drivers, constructors and races.

""",

    "keywords":[
        'race winner',
        'finishing position',
        'podium',
        'points',
        'champion',
        'fastest lap',
        'race result',
        'milliseconds',
        'laps',
        'time',
        'positionOrder'
    ],

    
    "important_columns":[
        'raceId',
        'driverId',
        'constructorId',
        'position',
        'points',
        'fastestLap',
        'fastestLapTime',
        'fastestLapSpeed',
        'statusId'
    ]

    },
 
    "drivers":{
        "description": """
Stores Formula 1 driver information.
Contains driver first name, last name, nationality and date of birth.
""",

    "keywords":[
       'driver',
       'driver name',
       'nationality'
    ],
    
    "important_columns":[
       'driverId',
       'forename',
       'surname',
       'nationality',
       'dob'
    ]

    },

    "constructors":{
        "description": """
Stores Formula 1 constructor (team) information.
Contains constructor name and nationality.

""",

    "keywords":[
       'constructor',
       'team',
       'Ferrari',
       'Mercedes',
       'McLaren',
       'Red Bull',
       'Williams'
    ],
    
    "important_columns":[
       'constructorId',
       'name',
       'nationality'
    ]

    },

    "driverStandings":{
        "description": """
Stores Formula 1 driver championship standings after each race.
Contains driver ranking, points and wins.

""",

    "keywords":[
       'driver standings',
       'championship standings',
       'driver ranking',
       'championship leader'
    ],
    
    "important_columns":[
       'raceId',
       'driverId',
       'points',
       'position',
       'wins',
    ]

    },

    "constructorStandings":{
        "description": """
Stores Formula 1 constructor championship standings.
Contains constructor ranking, points and wins.

""",

    "keywords":[
       'constructor standings',
       'team standings',
       'constructor championship'
    ],
    
    "important_columns":[
       'raceId',
       'constructorId',
       'points',
       'position',
       'wins'
    ]

    },

    "qualifying":{
        "description": """
Stores Formula 1 qualifying session results.
Contains qualifying position and Q1, Q2 and Q3 lap times.

""",

    "keywords":[
       'qualifying',
       'pole position',
       'Q1',
       'Q2',
       'Q3'
    ],
    
    "important_columns":[
       'raceId',
       'driverId',
       'constructorId',
       'position',
       'q1',
       'q2',
       'q3'
    ]

    },

    "lapTimes":{
        "description": """
Stores lap-by-lap timing information.
Contains lap number, lap position and lap time.

""",

    "keywords":[
       'lap',
       'lap time',
       'fastest lap',
       'milliseconds'
    ],
    
    "important_columns":[
       'raceId',
       'driverId',
       'lap',
       'position',
       'time',
       'milliseconds',
    ]

    },

    "pitStops":{
        "description": """
Stores Formula 1 pit stop information.
Contains stop number, lap number and stop duration.
""",

    "keywords":[
        'pit stop',
        'stop duration',
        'pit strategy'
    ],
    
    "important_columns":[
       'raceId',
       'driverId',
       'stop',
       'lap',
       'duration',
       'milliseconds'
    ]

    },

    "status":{
        "description": """
Stores the final status of race results.
Contains whether the driver finished, retired, crashed or had a mechanical failure.

""",

    "keywords":[
       'race status',
       'finished',
       'accident',
       'retired',
       'mechanical failure'
    ],
    
    "important_columns":[
       'statusId',
       'status',
    ]

    },

    "constructorResults":{
        "description": """
Stores constructor points earned in each race.
Contains constructor points and race status.

""",

    "keywords":[
       'constructor race results',
       'constructor points',
       'team points'
    ],
    
    "important_columns":[
       'raceId',
       'constructorId',
       'points',
       'status'
    ]

    },

    "seasons":{
        "description": """
Stores Formula 1 seasons.
Contains the season year and the official season website.

""",

    "keywords":[
       'season',
       'Formula 1 season',
       'year'

    ],
    
    "important_columns":[
       'year',
       'url'
    ]

    }

}