from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name, get_intent_name, get_slot, get_slot_value, get_supported_interfaces
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard, StandardCard, Image
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective as APLRenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apla import RenderDocumentDirective as APLARenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import (SetValueCommand, ExecuteCommandsDirective)
from ask_sdk_core.utils.viewport import get_viewport_profile
import logging
from statshandlers import goal_hander, cleansheets_handler, foul_handler, yellowcard_handler, redcard_handler, touches_handler, tackles_handler, referees_handler
from statshandlers import results_handler, fixtures_handler, table_handler, relegation_handler, team_handler,  team_results_or_fixtures, table_data, reload_main_table_as_needed
from statshandlers import NAME_INDEX,GOAL_DIFF_INDEX, find_team_index,load_combined_stats, load_two_stats
from shared import extra_cmd_prompts,  doc, noise, noise2, noise3, noise_max_millis 
from shared import noise2_max_millis, noise3_max_millis, datasources2, datasourcessp, test_speach_data, noise_data, teamsdatasource
from linechartdata import linedata
import boto3
from random import randrange
from QuickChart import QuickChart
from datetime import datetime
from statshandlers import wrap_language, set_translation, is_spanish


bucket = "bpltables"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
TOKEN = "buttontoken"
TICK_WIDTH = 3.0



def goaldifference(handler_input):
    _ = set_translation(handler_input)
    ds = get_goal_difference_url()
    response = boto3.client("cloudwatch").put_metric_data(
        Namespace='PremierLeague',
        MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
    )

    logger.info(ds)
    return (
        handler_input.response_builder
            .speak(wrap_language(handler_input, _("Here are the goal differences, press Back to return")))
            .set_should_end_session(False)          
            .add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = {
                    "type" : "Link",
                    "token" : TOKEN,
                    "src"  : "doc://alexa/apl/documents/GoalDifference"
                },
               # datasources = {"source": {"url": ds}}
                datasources = {"source": {"url": ds, "back": _("Back")}}
                    
              )
            ).response
        )
    
    
def savepercent(handler_input):
    _ = set_translation(handler_input)
    ds = get_save_percent_url(handler_input)
    response = boto3.client("cloudwatch").put_metric_data(
        Namespace='PremierLeague',
        MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
    )

    logger.info(ds)
    return (
        handler_input.response_builder
            .speak(wrap_language(handler_input, _("Here are Keeper saves versus goals, press Back to return")))
            .set_should_end_session(False)          
            .add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = {
                    "type" : "Link",
                    "token" : TOKEN,
                    "src"  : "doc://alexa/apl/documents/GoalDifference"
                },
                #datasources = {"source": {"url": ds}}
                datasources = {"source": {"url": ds, "back": _("Back")}}
                    
              )
            ).response
        )

def goals_shots(handler_input):
    logger.info("at goals_shots")
    _ = set_translation(handler_input)
    ds = get_goals_shots_url(handler_input)
    logger.info(f"ds in goals_shots is {ds}")
    response = boto3.client("cloudwatch").put_metric_data(
        Namespace='PremierLeague',
        MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
    )

    logger.info(ds)
    return (
        handler_input.response_builder
            .speak(wrap_language(handler_input, _("Here are goals vs shots, press Back to return")))
            .set_should_end_session(False)          
            .add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = {
                    "type" : "Link",
                    "token" : TOKEN,
                    "src"  : "doc://alexa/apl/documents/GoalDifference"
                },
                datasources = {"source": {"url": ds, "back": _("Back")}}
                    
              )
            ).response
        )
    
    
''' goal difference '''
def get_goal_difference_url():
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    names = []
    gds = []
    reload_main_table_as_needed()
    
    for index in range(0,20):
        name = table_data[index][NAME_INDEX]
        gd = table_data[index][GOAL_DIFF_INDEX]
        names.append(name)
        gds.append(gd)
    dict = {
        "type": "horizontalBar", 
        "data": {"labels": [], 
                "datasets": [{}]
        },
        "options":{
        "title": {
          "display": "false",
          "text": _("Goal Differences")
        }
      }    
    }
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = gds
    dict["data"]["datasets"][0]["label"] = "Goal Differences"
    dict["data"]["datasets"][0]["backgroundColor"] = 12345
    dict["data"]["datasets"][0]["borderColor"] = 12345
    dict["data"]["datasets"][0]["borderWidth"] = 1
    qc.config = str(dict).replace('12345', "function(context) {var index = context.dataIndex; var value = context.dataset.data[index];return value < 0 ? 'red' : 'blue';}")
    logger.info(qc.config)

    ret_url = qc.get_short_url()
    return(ret_url)


def get_line_chart_url(session_attr, handler_input):
    _ = set_translation(handler_input)
    #only do this the first time through ....
    if session_attr.get("first_time_graph", None) is None:
        session_attr["Liverpool"] = True
        session_attr["first_time_graph"] = True
    response = boto3.client("cloudwatch").put_metric_data(
        Namespace='PremierLeague',
        MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
    )

    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    form_data, highest_point, most_games_played = get_team_points_and_max_points()
    dict = {"type": "line", "data":{}}
    dict["data"]["labels"] = []
    dict["data"]["datasets"] = []
    dict["options"] = {
            "responsive": "true",
            "title": {
              "display": "true",
              "text": _("Team Points By Week")
            },
            "legend": { 
                "position": "top",
                "labels": {
                    "position": "right",
                    "boxWidth": 10,
                    "fontSize": 8
                }  
                
            }    

        }
    
    team_count = 0
    for team, points in form_data.items():
        name = session_attr.get(team, None)
        if name is not None:
            team_count += 1    
    for x in range(most_games_played):
        dict["data"]["labels"].append(str(x))
    rgb = 'rgb(255, 99, 132)'    
    color_index = 0
    for team, points in form_data.items():
        name = session_attr.get(team, None)
        if name is not None:
            rgb = team_colors.get(team, None)
            if rgb is None:
                logger.info(f"did not find color for {team}")
                rgb = graph_colors[color_index]
                color_index += 1
                if color_index >= len(graph_colors):
                    color_index = 0
            logger.info(f"Team {team} is active, get its points and graph it")
            this_team = form_data.get(team, "not found")
            if team_count < 6:
                team_dict = {'label': short_names[team], 'backgroundColor': rgb, 'borderColor':rgb, 'fill': False, 'data': []}
            else:
                team_dict = {'label': short_names[team], 'backgroundColor': rgb, 'borderColor':rgb, 'borderDash': team_dash.get(team,[]), 'fill': False, 'data': []}
            for point in points:
                team_dict['data'].append(point)
            logger.info(f"team is {str(team_dict)}")
            dict['data']['datasets'].append(team_dict)
    qc.config = dict
    ret_url = qc.get_short_url()
    logger.info(qc.config)
    return(ret_url)

team_dash = {
    "Arsenal": [1,1],
    "Aston Villa": [1,1], 
    "Brentford":[],
    "Brighton and Hove Albion": [], 
    "Burnley": [], 
    "Chelsea": [],
    "Crystal Palace": [1,1], 
    "Everton": [], 
    "Leeds United": [],
    "Leicester City": [1,1], 
    "Liverpool": [1,1],
    "Manchester City": [],
    "Manchester United": [], 
    "Newcastle United": [1,1], 
    "Norwich City": [1,1],
    "Southampton": [1,1], 
    "Tottenham Hotspur": [],
    "Watford": [], 
    "West Ham United": [], 
    "Wolverhampton Wanderers": [1,1] 
    
}
team_colors = {
    "Arsenal": "#EF0107",
    "Aston Villa": "#95BFE5", 
    "Brentford": "#fbb800",
    "Brighton and Hove Albion": "#0057B8", 
    "Burnley": "#6C1D45", 
    "Chelsea": "#034694",
    "Crystal Palace": "#1B458F", 
    "Everton": "#003399", 
    "Leeds United": "#FFCD00",
    "Leicester City": "#003090", 
    "Liverpool": "#003090",
    "Manchester City": "#6CABDD",
    "Manchester United": "#DA291C", 
    "Newcastle United": "#241F20", 
    "Norwich City": "#FFF200",
    "Southampton": "#D71920", 
    "Tottenham Hotspur": "#132257",
    "Watford": "#FBEE23", 
    "West Ham United": "#7A263A", 
    "Wolverhampton Wanderers": "#FDB913" 
}
def do_line_graph(handler_input):
    _ = set_translation(handler_input)
    ds = get_line_chart_url(handler_input.attributes_manager.session_attributes, handler_input)

    logger.info(ds)
    return (
        handler_input.response_builder
            .speak(wrap_language(handler_input, _("Team points by week, say add or remove team")))
            .set_should_end_session(False)          
            .add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = {
                    "type" : "Link",
                    "token" : TOKEN,
                    "src"  : "doc://alexa/apl/documents/GoalDifference"
                },
                datasources = {"source": {"url": ds, "back": _("Back")}}
                    
              )
            ).response
        )

    

def get_save_percent_url(handler_input):
    _ = set_translation(handler_input)
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    names, goals, saves = load_combined_stats(5,"savepercent",1,2,4)

    dict = {
        "type": "bar", 
        "data": {
            "labels": [], 
                "datasets": [
                    {
                        "label": _("Saves"),
                        "backgroundColor": 'rgb(75, 192, 192)',
                        "stack": "Stack 0",
                        "data":[]
                    },
                    {
                        "label":_("goals allowed"),
                        "backgroundColor": 'rgb(255,99,132)',
                        "stack": "Stack 1",
                        "data":[]
                    }
                ]
        },
        "options":{
            "responsive": "true",
            "title": {
              "display": "true",
              "text": _("Keeper Saves vs. Goals")
            },
            "scales": {
                "xAxes": [ { "stacked": "true"}],
                "yAxes": [ { "stacked": "true"}],
            }
      }    
    }
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = saves
    dict["data"]["datasets"][1]["data"] = goals
    qc.config = str(dict)

    ret_url = qc.get_short_url()
    logger.info(f"the long url is {qc.get_url()}")
    return(ret_url)


def get_goals_shots_url(handler_input):
    _ = set_translation(handler_input)
    logger.info("at get_goals_shots_url")
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    names, goals, shots = load_two_stats(5,"goals_shots")
    logger.info("after load_two_")
    dict = {
        "type": "bar", 
        "data": {
            "labels": [], 
                "datasets": [
                    {
                        "label": _("Goals"),
                        "backgroundColor": 'rgb(75, 192, 192)',
                        "stack": "Stack 0",
                        "data":[]
                    },
                    {
                        "label":_("Shots"),
                        "backgroundColor": 'rgb(255,99,132)',
                        "stack": "Stack 1",
                        "data":[]
                    }
                ]
        },
        "options":{
            "responsive": "true",
            "title": {
              "display": "true",
              "text": _("Goals vs Shots")
            },
            "scales": {
                "xAxes": [ { "stacked": "true"}],
                "yAxes": [ { "stacked": "true"}],
            }
      }    
    }
    logger.info("after set dict")
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = goals
    dict["data"]["datasets"][1]["data"] = shots
    qc.config = str(dict)

    ret_url = qc.get_short_url()
    logger.info(f"the long url is {qc.get_url()}")
    return(ret_url)


def go_home(handler_input):
    _ = set_translation(handler_input)
    if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
        return (
            handler_input.response_builder
                .speak(wrap_language(handler_input, _("Welcome to Premier League, press a button or scroll to see more options")))
                .set_should_end_session(False)          
                .add_directive( 
                  APLRenderDocumentDirective(
                    token= "developer-provided-string",
                    document = {
                        "type" : "Link",
                        "token" : "my token",
                        "src"  : "doc://alexa/apl/documents/GridList"
                    },
                    datasources = datasourcessp if is_spanish(handler_input) else datasources2 
                  )
                ).response
            )
    else:
        return(handler_input.response_builder.speak(_("This device does not have a screen, what can we help you with")).ask(_("what can we help you with")).response)

        
class ButtonEventHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        logger.info("at can handle ButtonEventHandler")
        if is_request_type("Alexa.Presentation.APL.UserEvent")(handler_input):
            user_event = handler_input.request_envelope.request
            return True
        else:
            return False
 
    def handle(self, handler_input):
        _ = set_translation(handler_input)
        logger.info("at ButtonEventHandler")
        SELECTED_COLOR = "white"
        UNSELECTED_COLOR = "grey"
        
        first_arg = handler_input.request_envelope.request.arguments[0]
        logger.info(f"first_arg was {first_arg}")
        
        if first_arg == 'radioButtonText':
            radio_button_id   = handler_input.request_envelope.request.arguments[1]['radioButtonId']
            radio_button_text = handler_input.request_envelope.request.arguments[1]['radioButtonText']
            logger.info(f"about to send an ExecuteCommands based on {handler_input.request_envelope.request.arguments[1]['radioButtonId']}")
            buttons = ["Form","Results","Fixtures"]
            texts   = [_("ShowTeamForm"),_("ShowTeamResults"),_("ShowTeamFixtures")]
            button_commands = []
            
            # for each button turn it on/off based on what was picked
            for button, button_text in zip(buttons,texts):  
                value = SELECTED_COLOR if handler_input.request_envelope.request.arguments[1]['radioButtonId'] == button else UNSELECTED_COLOR
                set_value_command = SetValueCommand(component_id=button,object_property="radioButtonColor",value=value)
                button_commands.append(set_value_command)
                
                logger.info(f"setting {button_text} to {value}")
                set_value_command = SetValueCommand(component_id=button_text,object_property="color",value=value)
                button_commands.append(set_value_command)

                value = True if handler_input.request_envelope.request.arguments[1]['radioButtonId'] == button else False
                if value == True:
                    # remember what button was selected for the next event
                    session_attr = handler_input.attributes_manager.session_attributes
                    session_attr["radioButtonText"] = handler_input.request_envelope.request.arguments[1]['radioButtonId']
                    handler_input.attributes_manager.session_attributes = session_attr

                set_value_command = SetValueCommand(component_id=button,object_property="checked",value=value)
                button_commands.append(set_value_command)
            return (handler_input.response_builder.speak(wrap_language(handler_input, _("Ok, we'll show you team {}")).format(radio_button_id)).add_directive(ExecuteCommandsDirective(token=TOKEN,commands=button_commands)).response)
        
        if first_arg == "goaldifference":
            return(goaldifference(handler_input))

        if first_arg == "savepercent":
            return(savepercent(handler_input))
            
        if first_arg == "goals_shots":
            return(goals_shots(handler_input))
            
 
        if first_arg == "line":
            #return(load_and_output_graph(handler_input, linedata))
            return(do_line_graph(handler_input))

        if first_arg == "goBack":
            return(go_home(handler_input))
        
        if first_arg == "Leave a Review":
            handler_input.response_builder.speak("Scan this QR code with your phone to leave us a review, thank you!").ask(HELP_REPROMPT)
            return handler_input.response_builder.response
            
            
        if first_arg == "teams":
            this_profile = str(get_viewport_profile(handler_input.request_envelope))
            item_heights = {"ViewportProfile.HUB_LANDSCAPE_SMALL": "75%", "ViewportProfile.HUB_LANDSCAPE_MEDIUM": "65%", "ViewportProfile.HUB_LANDSCAPE_LARGE": "55%"}
            this_height = item_heights.get(this_profile, "")
            teamsdatasource["gridListData"]["listItemHeight"] = this_height
            teamsdatasource["gridListData"]["title"] = _("You can ask about each team")
            teamsdatasource["radioButtonExampleData"]["radioButtonGroupItems"][0]["radioButtonText"] = _("ShowTeamForm")
            teamsdatasource["radioButtonExampleData"]["radioButtonGroupItems"][1]["radioButtonText"] = _("ShowTeamResults")
            teamsdatasource["radioButtonExampleData"]["radioButtonGroupItems"][2]["radioButtonText"] = _("ShowTeamFixtures")
            logger.info("teamsdatasource")
            logger.info(str(teamsdatasource))
            return (
                handler_input.response_builder
                    .speak(wrap_language(handler_input, _("Here is the page of just teams")))
                    .set_should_end_session(False)          
                    .add_directive( 
                      APLRenderDocumentDirective(
                        token= TOKEN,
                        document = {
                            "type" : "Link",
                            "token" : TOKEN,
                            "src"  : "doc://alexa/apl/documents/RadioButtons"
                        },
                        datasources = teamsdatasource 
                      )
                    ).response
                )
            
        session_attr = handler_input.attributes_manager.session_attributes

        # if we get here it was an actual button press so we should say something

        vector_table = {"goals"      : goal_hander, 
                        "cleansheet" : cleansheets_handler, 
                        "fouls"      : foul_handler, 
                        "yellowcard" : yellowcard_handler,
                        "redcard"    : redcard_handler,
                        "touches"    : touches_handler,
                        "tackles"    : tackles_handler,
                        "referee"    : referees_handler,
                        "results"    : results_handler,
                        "fixtures"   : fixtures_handler,
                        "table"      : table_handler,
                        "relegation" : relegation_handler
        }
        logger.info(f"the button that was pressed was {first_arg}")
        if first_arg in vector_table:
            return vector_table.get(first_arg)(handler_input)
        else:
            verb = session_attr.get("radioButtonText", "")
            logger.info(f"the verb when a team button was pressed was {verb}")
            if verb == "Fixtures":
                return team_results_or_fixtures(handler_input, first_arg, "fixtures2")
            elif verb == "Results":
                return team_results_or_fixtures(handler_input, first_arg, "prevWeekFixtures")
            else:
                return(team_handler(handler_input, first_arg))
                

'''
Return the array of team data points and the highest point total of any team (for the Y-axis)
'''
def get_team_points_and_max_points():
    s3 = boto3.client("s3")
    resp = s3.get_object(Bucket=bucket, Key="line_data")
    body_str = string_data = resp['Body'].read().decode("utf-8")
    logger.info("converted streaming_body to string")
    n = body_str.split("\n")
    n.pop()
    lines_in_file = len(n)
    form_data = {}
    highest_point = 0
    most_games_played = 0
    
    for line in n:
        logger.info(f"line is {line}")
        this_line = line.split(',')
        team_points = this_line[1:]
        if len(team_points) > most_games_played:
            most_games_played = len(team_points)
        form_data[this_line[0]] = team_points
        this_teams_total = int(this_line[-1])
        if this_teams_total > highest_point:
            highest_point = this_teams_total
            
    logger.info("highest point is " + str(highest_point))
    return form_data, highest_point, most_games_played

'''
blue	rgb(0,0,255)
green	rgb(0,128,0)
lime	rgb(0,255,0)
aqua	rgb(0,255,255)
silver	rgb(192,192,192)
red	    rgb(255,0,0)
yellow	rgb(255,255,0)
'''
graph_colors = [
"rgb(0,0,255)",
"rgb(0,128,0)",
"rgb(0,255,0)",
"rgb(0,255,255)",
"rgb(192,192,192)",
"rgb(255,0,0)",
"rgb(255,255,0)"
]

def random_color():
    return f"rgba({randrange(255)},{randrange(255)},{randrange(255)},1)"
    

class AddTeamIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AddTeamIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("Add handler")
        return(add_or_delete_team(handler_input, "add"))

class RemoveTeamIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("RemoveTeamIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("Remove handler")
        return(add_or_delete_team(handler_input, "remove"))

def team_in_chart(session_attr,team):
    name = session_attr.get(team, None)
    return False if name is None else True

    
'''
The voice model has one slot but that slot is marked as can accept multiple values.
So, the slot value might be in one part of the handler_input or a different part
'''
def add_or_delete_team(handler_input, mode):
    _ = set_translation(handler_input)
    if get_supported_interfaces(handler_input).alexa_presentation_apl is None:
        logger.info(f"{mode} on a device without a screen, give error")
        response = _("Sorry, adding or removing teams for the graph is only supported on devices with screens.")
        reprompt = _(" What can we tell you about premier league?")
        return (
            handler_input.response_builder
                .ask(reprompt)
                .speak(response + reprompt).response
        )
    prompt = None
    
    slot = get_slot(handler_input, "plteam")
    if slot.resolutions is not None:    # there is only one slot value
        dict = slot.resolutions.to_dict()
        logger.info("-------")
        logger.info(str(dict['resolutions_per_authority'][0]['status']['code']))
        if dict['resolutions_per_authority'][0]['status']['code'] == "ER_SUCCESS_NO_MATCH":
            logger.info("no matching team found")
            handler_input.response_builder.speak("Sorry, I could not find that team, please say add or remove team").ask("Please try again")
            return handler_input.response_builder.response
        logger.info("Team name is: " + dict['resolutions_per_authority'][0]["values"][0]["value"]["name"])
        team = dict['resolutions_per_authority'][0]["values"][0]["value"]["name"]
        session_attr = handler_input.attributes_manager.session_attributes
        if mode == "add":
            session_attr[team] = True
            #prompt = "added {} to the graph".format(team)
        else:
            session_attr.pop(team, "not found ")
            logger.info(f"removed {team} from the session and its still there?: {team_in_chart(session_attr,team)}")
            #prompt = "removed {} from the graph".format(team)
        handler_input.attributes_manager.session_attributes = session_attr
        return((do_line_graph(handler_input)))   #(do_line_graph(handler_input))

    else:  # there are multiple slot values
        session_attr = handler_input.attributes_manager.session_attributes
        prompt = mode + "ed "
        if slot.slot_value is not None:
            for value in slot.slot_value.values:
                logger.info("Team Name: " + str(value.resolutions.resolutions_per_authority[0].values[0].value.name))
                team = str(value.resolutions.resolutions_per_authority[0].values[0].value.name)
                if mode == "add":
                    session_attr[team] = True
                    logger.info(f"added {team} to the session")
                    prompt += team
                else:
                    session_attr.pop(team, "not found 2")
                    logger.info(f"removed {team} to the session and its still there?: {team_in_chart(session_attr,team)}")
                    prompt += team
        handler_input.attributes_manager.session_attributes = session_attr
        return((do_line_graph(handler_input)))
        
short_names = {
    #"as appears in table" : "as appears in results"
    "Arsenal"           : "Arsenal",
    "Aston Villa"       : "Villa",
    "Burnley"           : "Burnley",
    "Brentford"         : "Brentford",
    "Brighton and Hove Albion" : "Brighton",
    "Chelsea"           : "Chelsea",
    "Crystal Palace"    : "Palace",
    "Everton"           : "Everton",
    "Leeds United"      : "Leeds",
    "Leicester City"    : "Leicester",
    "Liverpool"         : "Liverpool",
    "Manchester United" : "Man United",
    "Manchester City"   : "Man City",
    "Newcastle United"  : "Newcastle",
    "Norwich City"      : "Norwich",
    "Southampton"       : "Southampton",
    "Tottenham Hotspur" : "Spurs", 
    "Watford"           : "Watford",
    "West Ham United"    : "West Ham",
    "Wolverhampton Wanderers" : "Wolves"
}        
