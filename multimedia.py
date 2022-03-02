from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name, get_intent_name, get_slot, get_slot_value, get_supported_interfaces
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.services.directive import (SendDirectiveRequest, Header, SpeakDirective)
from ask_sdk_model.ui import SimpleCard, StandardCard, Image
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective as APLRenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apla import RenderDocumentDirective as APLARenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import (SetValueCommand, ExecuteCommandsDirective)
from ask_sdk_core.utils.viewport import get_viewport_profile
import logging
from statshandlers import goal_hander, cleansheets_handler, foul_handler, yellowcard_handler, redcard_handler, touches_handler, tackles_handler, referees_handler
from statshandlers import load_stats_ng
from statshandlers import results_handler, fixtures_handler, table_handler, relegation_handler, team_handler,  team_results_or_fixtures, table_data, reload_main_table_as_needed
from statshandlers import NAME_INDEX,GOAL_DIFF_INDEX, find_team_index,load_combined_stats, load_two_stats
from shared import extra_cmd_prompts,  doc, noise, noise2, noise3, noise_max_millis, real_results_table 
from shared import noise2_max_millis, noise3_max_millis, datasources2, datasourcessp, test_speach_data, noise_data, teamsdatasource, foo_table, results_table, championship_table
from shared import other_leagues,noises, statistics, basic_charts, advanced_charts
from linechartdata import linedata
import boto3
import json
from random import randrange
from QuickChart import QuickChart
from datetime import datetime
from statshandlers import wrap_language, set_translation, is_spanish, day_of_week_trans,month_trans, load_champ_table, champ_table
from statshandlers import emit_locale_metric, return_random_noise
import traceback
import copy
import time
from isp import skill_has_products, list_purchasable_products, buy_product, ds2_advanced_or_not

bucket = "bpltables"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
TOKEN = "buttontoken"
TICK_WIDTH = 3.0

'''
ButtonEventHandler
go_home
special_shorten
results_visual
fix_logo_name
fixtures_visual
table
goaldifference
get_goal_difference_url
yellow_red
savepercent
get_save_percent_url
goals_shots
get_goals_shots_url
get_line_chart_url
do_line_graph
get_team_points_and_max_points
AddTeamIntentHandler
RemoveTeamIntentHandler
add_or_delete_team
'''
        
class ButtonEventHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        #logger.info("at can handle ButtonEventHandler")
        if is_request_type("Alexa.Presentation.APL.UserEvent")(handler_input):
            user_event = handler_input.request_envelope.request
            return True
        else:
            return False
 
    def handle(self, handler_input):
        _ = set_translation(handler_input)
        #logger.info("at ButtonEventHandler")
        SELECTED_COLOR = "white"
        UNSELECTED_COLOR = "grey"
        emit_locale_metric(handler_input)
        
        first_arg = handler_input.request_envelope.request.arguments[0]
        logger.info(f"first_arg was {first_arg}")
        response = boto3.client("cloudwatch").put_metric_data(
            Namespace='PremierLeague',
            MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
        )
        boto3.client("cloudwatch").put_metric_data(
                    Namespace='PremierLeague',
                    MetricData=[
                        {
                            'MetricName': 'visualbuttons',
                            'Dimensions': [{ 'Name': 'button','Value': first_arg},],
                            'Value': 1,
                            'Unit': 'Count'
                        },
                    ]
                )
        
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
                
                #logger.info(f"setting {button_text} to {value}")
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
                direct_object = radio_button_id
                if is_spanish(handler_input):
                    direct_object = direct_object.replace("Fixtures","Encuentros").replace("Results","Resultados").replace("Form","Forma")
            logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} {direct_object}")
            return (handler_input.response_builder.speak(wrap_language(handler_input, _("Ok, we'll show you team {}")).format(direct_object)).add_directive(ExecuteCommandsDirective(token=TOKEN,commands=button_commands)).response)

        if first_arg == "purchase":
            the_text = "A set of advanced analytic graphs are available including Vee Eh Are, Attendance, Corners, Possession, Long vs short goals, and Offside, say, purchase advanced, to give them a try"
            logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} {the_text}")
            return handler_input.response_builder.speak(the_text).ask("press a button").response
            
        if first_arg == "goaldifference":
            return(goaldifference(handler_input))

        if first_arg == "savepercent":
            return(savepercent(handler_input))
            
        if first_arg == "goals_shots":
            return(goals_shots(handler_input))

        purchase_only = ["attendance", "possession", "in_out_box", "corners", "offside", "var", "rankchanges"]
        if (first_arg in purchase_only) and (skill_has_products(handler_input) is None):
            the_text = "that button requires a subscription, say, purchase advanced, to give the advanced analytic charts a try"
            return handler_input.response_builder.speak(the_text).ask("press a button").response
                
        if first_arg == "attendance":
            return(attendance(handler_input))
            
        if first_arg == "possession":
            return(possession(handler_input))
            
        if first_arg == "in_out_box":
            return(in_out_box(handler_input))
            
        if first_arg == "corners":
            return(corners(handler_input))
            
        if first_arg == "offside":
            return(offside(handler_input))
            
        if first_arg == "var":
            return(var(handler_input))
            
        if first_arg == 'allteams':
            load_group_to_line_chart(handler_input.attributes_manager.session_attributes, handler_input, 0, 20)
            return(do_line_graph(handler_input))
        if first_arg == 'topsix':
            load_group_to_line_chart(handler_input.attributes_manager.session_attributes, handler_input, 0, 6)
            return(do_line_graph(handler_input))
        if first_arg == 'relzone':
            load_group_to_line_chart(handler_input.attributes_manager.session_attributes, handler_input, 14, 20)
            return(do_line_graph(handler_input))
        if first_arg == 'midtable':
            load_group_to_line_chart(handler_input.attributes_manager.session_attributes, handler_input, 6, 14)
            return(do_line_graph(handler_input))
            
        if first_arg == "line":
            return(do_line_graph(handler_input))

        if first_arg == "goBack":
            return(go_home(handler_input))
            
        if first_arg == "table":
            return(table(handler_input))
        
        if first_arg == "championship":
            return(championship_visual(handler_input))
        
        if first_arg == "bundesliga":
            return(bundesliga_visual(handler_input))
            
        if first_arg == "laliga":
            return(laliga_visual(handler_input, "laliga", "la liga"))
            
        if first_arg == "serie_a":
            return(laliga_visual(handler_input, "serie_a", "serie eh"))

        if first_arg == "Leave a Review":
            if is_spanish(handler_input):
                text = "Escanee este código QR con su teléfono para dejarnos una reseña, gracias"
                HELP_REPROMPT = 'Qué podemos ayudarte'
            else:
                text = "Scan this QR code with your phone to leave us a review, thank you!"
                HELP_REPROMPT = 'What can  we help you with?'
            handler_input.response_builder.speak(text).ask(HELP_REPROMPT)
            return handler_input.response_builder.response
            
        if first_arg == "referee":
            if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
                return yellow_red(handler_input)

        if first_arg == "fixtures":
            return fixtures_visual(handler_input)
            
        if first_arg == "results":
            return results_visual(handler_input)

        if first_arg == "rankchanges":
            return rankchanges(handler_input)

        if first_arg == "statistics":
            return secondary_page(handler_input, _("You can ask about ..."), _("Here are some statistics"), statistics)
            # logger.info("bring up secondary page")
            # other_leagues["gridListData"]["title"] = _("You can ask about ...")
            # return (
            #     handler_input.response_builder
            #         .speak(wrap_language(handler_input, _("Here are some statistics")))
            #         .set_should_end_session(False)          
            #         .add_directive( 
            #           APLRenderDocumentDirective(
            #             token= TOKEN,
            #             document = {
            #                 "type" : "Link",
            #                 "token" : TOKEN,
            #                 "src"  : "doc://alexa/apl/documents/GridList"
            #             },
            #             datasources = statistics 
            #           )
            #         ).response
            #     )

        if first_arg == "basic_charts" or first_arg == "goBackBasicCharts":
            return secondary_page(handler_input, _("Here are some charts"), _("Here are some charts"), basic_charts)
            
        if first_arg == "advanced_charts" or first_arg == "goBackAdvancedCharts":
            if skill_has_products(handler_input) is None:
                logger.info("you need to purchase that")
                the_text = "that button requires a subscription, say, purchase advanced, to give the advanced analytic charts a try"
                return handler_input.response_builder.speak(the_text).ask("press a button").response
            else:    
                return secondary_page(handler_input, _("Here are some advanced charts"), _("Here are some advanced charts"), advanced_charts)

        if first_arg == "other_leagues":
            return secondary_page(handler_input, _("You can ask about ..."), _("Here are the tables for other leagues"), other_leagues)
            # logger.info("bring up secondary page")
            # other_leagues["gridListData"]["title"] = _("You can ask about ...")
            # return (
            #     handler_input.response_builder
            #         .speak(wrap_language(handler_input, _("Here are the tables for other leagues")))
            #         .set_should_end_session(False)          
            #         .add_directive( 
            #           APLRenderDocumentDirective(
            #             token= TOKEN,
            #             document = {
            #                 "type" : "Link",
            #                 "token" : TOKEN,
            #                 "src"  : "doc://alexa/apl/documents/GridList"
            #             },
            #             datasources = other_leagues 
            #           )
            #         ).response
            #     )
            
        if first_arg == "teams":
            this_profile = str(get_viewport_profile(handler_input.request_envelope))
            item_heights = {"ViewportProfile.HUB_LANDSCAPE_SMALL": "75%", "ViewportProfile.HUB_LANDSCAPE_MEDIUM": "65%", "ViewportProfile.HUB_LANDSCAPE_LARGE": "55%"}
            this_height = item_heights.get(this_profile, "")
            teamsdatasource["gridListData"]["listItemHeight"] = this_height
            teamsdatasource["gridListData"]["title"] = _("You can ask about each team")
            teamsdatasource["radioButtonExampleData"]["radioButtonGroupItems"][0]["radioButtonText"] = _("ShowTeamForm")
            teamsdatasource["radioButtonExampleData"]["radioButtonGroupItems"][1]["radioButtonText"] = _("ShowTeamResults")
            teamsdatasource["radioButtonExampleData"]["radioButtonGroupItems"][2]["radioButtonText"] = _("ShowTeamFixtures")
            #logger.info("teamsdatasource")
            #logger.info(str(teamsdatasource))
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


def secondary_page(handler_input, title, prompt, datasource):
    try:
        logger.info("bring up secondary page " + prompt)
        logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} {title} {prompt}.")
        datasource["gridListData"]["title"] = title
        return (
            handler_input.response_builder
                .speak(wrap_language(handler_input, prompt))
                .set_should_end_session(False)          
                .add_directive( 
                  APLRenderDocumentDirective(
                    token= TOKEN,
                    document = {
                        "type" : "Link",
                        "token" : TOKEN,
                        "src"  : "doc://alexa/apl/documents/GridList"
                    },
                    datasources = datasource 
                  )
                ).response
        )
    except Exception as ex:
        logger.info("error displaying secondary page")
        logger.error(ex)
        traceback.print_exc()
    
    
def go_home(handler_input):
    _ = set_translation(handler_input)
    if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
        speech = _("Welcome to Premier League, press a button or scroll to see more options")
        logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} audio {speech}.")
        return (
            handler_input.response_builder
                .speak(wrap_language(handler_input, speech))
                .set_should_end_session(False)          
                .add_directive( 
                  APLRenderDocumentDirective(
                    token= "developer-provided-string",
                    document = {
                        "type" : "Link",
                        "token" : "my token",
                        "src"  : "doc://alexa/apl/documents/GridList"
                    },
                    datasources = datasourcessp if is_spanish(handler_input) else ds2_advanced_or_not(handler_input) 
                  )
                ).response
            )
    else:
        speech = _("This device does not have a screen, what can we help you with")
        prompt = _("what can we help you with")
        logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} go_home {speech} {prompt}.")
        return(handler_input.response_builder.speak(speech).ask(prompt).response)


def special_shorten(name):
    if name == "Southampton":
        return "Southmptn"
    return name


def results_visual(handler_input):
    LOGO1 = 0
    TEAM1 = 1
    SCORE = 2
    TEAM2 = 3
    LOGO2 = 4
    CFPREFIX = "https://duy7y3nglgmh.cloudfront.net/"
    _ = set_translation(handler_input)
    try:
        s3 = boto3.client("s3")
        bucket = "bpltables"
        resp = s3.get_object(Bucket=bucket, Key="prevWeekFixtures")
        body_str = resp['Body'].read().decode("utf-8")
        n = body_str.split("\n")
        
        for index in range(0,20):
            #logger.info(n[index])
            one_result = n[index].split(',')
            #logger.info(str(one_result))
            one_result[0] = one_result[0].replace(" lost to", "").replace(" beat", "").replace(" drew","")
            one_result[1] = one_result[1].replace(" to ", "-")
            team1 = one_result[0]
            team2 = one_result[2]
            score = one_result[1]
            #logger.info(f"team1:{team1} score:{score} team2:{team2}")
            
            real_results_table["dataTable"]["properties"]["rows"][index]["cells"][LOGO1]["text"] = CFPREFIX + fix_logo_name(team1) + ".png"
            real_results_table["dataTable"]["properties"]["rows"][index]["cells"][TEAM1]["text"] = team1
            real_results_table["dataTable"]["properties"]["rows"][index]["cells"][SCORE]["text"] = score
            real_results_table["dataTable"]["properties"]["rows"][index]["cells"][TEAM2]["text"] = team2
            real_results_table["dataTable"]["properties"]["rows"][index]["cells"][LOGO2]["text"] = CFPREFIX + fix_logo_name(team2) + ".png"
    except Exception as ex:
        logger.info("hit exception")
        logger.error(ex)        

    real_results_table["dataTable"]["back"] = _("Back")
    doc = _load_apl_document("resultstable.json")
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        try:
            doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["items"][0]["item"]["fontSize"] = "2vh"
        except Exception as ex:
            logger.info("could not get pixel_height")
            logger.error(ex)
            traceback.print_exc()
    rb = handler_input.response_builder
    speech = _("Here are the results, scroll down and press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                    document = doc,
                    datasources = real_results_table 
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} go_home {speech}.")
    return rb.response        

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are the results, scroll down and press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token = "developer-provided-string",
    #                 document = doc,
    #                 datasources = real_results_table 
    #           )
    #         ).response
    #     )
        
def fix_logo_name(name):
    #logger.info(f"fix .{name}.")
    if name == "Leicester":
        return ("LeicesterCity")
    elif name == "Wolverhampton":
        return "WolverhamptonWanderers"
    elif (name == "WestHam") or (name == "West Ham"):
        #logger.info("returning WestHamUnited")
        return "WestHamUnited"
    elif name == "Leeds":
        return "LeedsUnited"
    elif name == "Newcastle":
        return "NewcastleUnited"
    elif name == "Tottenham":
        return "TottenhamHotspur"
    elif name == "Brighton":
        return "BrightonAndHoveAlbion"
    elif " " in name:
        return name.replace(" ", "")
    else:
        return name


def load_fixture_data(handler_input):
    lines_to_display = 35
    table_index = 0
    speech, ignore = load_stats_ng(handler_input, lines_to_display, "fixtures2", ".", ".", ";", 0, 2, 1, "")
    first_split = speech.split(";")
    logger.info("load_fixture_data")
    try:
        for s in first_split:
            for s2 in s.split(","):
                if(len(s2) > 0):
                    if('.' not in s2):
                        results_table["dataTable"]["properties"]["rows"][table_index]["backgroundColor"] = "grey"
                        try:
                            date_split = x = s2[1:].split(' ')
                            logger.info("inside inner loop " + str(date_split))
                            foo = day_of_week_trans(handler_input,date_split[0])
                            bar = month_trans(handler_input, foo)
                            month1 = day_of_week_trans(handler_input,date_split[2])
                            month2 = month_trans(handler_input,month1)
                            logger.info("after translations, bar is " + str(bar))
                            results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] = bar
                            results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] = date_split[1]
                            results_table["dataTable"]["properties"]["rows"][table_index]["cells"][1]["text"] = month2
                            
                            if results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] == "after":
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][1]["text"] = "after"
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] = "tomorrow"
                            if results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] == "tomorrow":
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] = ""
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][1]["text"] = "tomorrow"
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] = ""
                            if results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] == "today":
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] = ""
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][1]["text"] = "today"
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] = ""
                            logger.info("foo")
                            logger.info(results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"]) 
                        except Exception as ex:
                            logging.info("possible special date " )
                            special_date = s2[1:]
                            if special_date == "today" or special_date == "tomorrow":
                                logging.info("today or tomorrow")
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] = ""
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] = ""
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][1]["text"] = special_date
                            else:
                                logger.info("day after tomorrow")
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][0]["text"] = special_date
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][1]["text"] = special_date
                                results_table["dataTable"]["properties"]["rows"][table_index]["cells"][2]["text"] = special_date
                        logger.info("setting a date " + s2 + " at index " + str(table_index))
                        table_index += 1
                    else:
                        line = ""
                        results_table["dataTable"]["properties"]["rows"][table_index]["backgroundColor"] = "purple"
                        sub_index = 0
                        for s3 in s2.split('.'):
                            s3 = s3.replace('"', '').replace("oh clock", "00")
                            if sub_index == 2:
                                s3 = s3.replace(" ", ":")
                            results_table["dataTable"]["properties"]["rows"][table_index]["cells"][sub_index]["text"] = s3
                            results_table["dataTable"]["properties"]["rows"][table_index]["cells"][sub_index]["fontSize"] = "5vh"
                            sub_index += 1
            table_index += 1
    except Exception as ex:
        logger.info("hit exception in load_fixture_data")
        logger.error(ex)        
        traceback.print_exc()
    
    
def fixtures_visual(handler_input):
    try:
        logger.info("at fixtures_visual")
        _ = set_translation(handler_input)
        load_fixture_data(handler_input)
        
    except Exception as ex:
        logger.info("hit exception in fixtures_visual")
        logger.error(ex)        
        traceback.print_exc()
    
    try:
        results_table["dataTable"]["back"] = _("Back")
        doc = _load_apl_document("table2.json")
        if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
            logger.info("RUNNING on 15 inch portrait")
            try:
                doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["items"][0]["item"]["fontSize"] = "2vh"
                #doc["mainTemplate"]["items"][0]["item"]["items"][1]["items"][0]["items"][0]["item"]["fontSize"] = "2vh"
            except Exception as ex:
                logger.info("could not get pixel_height")
                logger.error(ex)
                traceback.print_exc()
        rb = handler_input.response_builder
        speech = _("Here are the fixtures, press Back to return")
        rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
        rb.add_directive( 
                  APLRenderDocumentDirective(
                        document = doc,
                        datasources = results_table 
                  )
                )
        add_noise_directive(rb)        
        logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} go_home {speech}.")
        return rb.response        
    except Exception as ex:
        logger.info("hit exception2 in fixtures_visual")
        logger.error(ex)        
        traceback.print_exc()


''' converted to have background sound ''' 
def laliga_visual(handler_input, key, text):
    bun_table = []
    _ = set_translation(handler_input)
    logger.info("at laliga table chart")
    s3 = boto3.client("s3")
    resp = s3.get_object(Bucket="bpltables", Key=key)
    body_str = resp['Body'].read().decode("utf-8")
    x = body_str.split("\n")
    team_index = 0
    bar = copy.deepcopy(foo_table)
    bar["dataTable"]["back"] = _("Back")
    bar["dataTable"]["properties"]["headings"][1] = _("Team")
    bar["dataTable"]["properties"]["headings"][2] = _("Games")
    bar["dataTable"]["properties"]["headings"][3] = _("wins")
    bar["dataTable"]["properties"]["headings"][4] = _("draws")
    bar["dataTable"]["properties"]["headings"][5] = _("losses")
    bar["dataTable"]["properties"]["headings"][9] = _("Points")

    for team in x:
        try:
            #logger.info(f"about to do team {team_index}")
            if team_index < 4:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "green"
            elif team_index < 6:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "blue"
            elif team_index > 16:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "red"
                
            one_team = team.split(",")
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][0]["text"] = str(team_index+1)
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][1]["text"] = one_team[0]
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][2]["text"] = str(one_team[1])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][3]["text"] = str(one_team[2])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][4]["text"] = str(one_team[3])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][5]["text"] = str(one_team[4])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][6]["text"] = str(one_team[5])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][7]["text"] = str(one_team[6])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][8]["text"] = str(one_team[7])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][9]["text"] = str(one_team[8])
            team_index = team_index + 1
            if team_index > 19:
                break
        except Exception as ex:
            logger.info("hit exception")
            logger.error(ex)
    #logger.info("about to do LaLiga or Seria A")
    doc = _load_apl_document("table.json")
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        try:
            doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
            doc["mainTemplate"]["items"][0]["item"]["items"][1]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
        except Exception as ex:
            logger.info("could not get pixel_height")
            logger.error(ex)
    rb = handler_input.response_builder
    speech = _("Here is the table, press Back to return")
    rb.speak(wrap_language(handler_input,speech)).set_should_end_session(False)
    rb.add_directive( 
              APLRenderDocumentDirective(
                token = "developer-provided-string",
                    document = doc,
                    datasources = bar 
              )
            )
    noise,start = return_random_noise()
    rb.add_directive( 
        APLARenderDocumentDirective(
            token= "developer-provided-string",
            document = _load_apl_document("justCrowdNoise.json"),
            datasources = {"text": {"speak": ""},
                "crowd": {
                    "noise": noise,
                    "start": str(start)
                }
            }              
        )
      )
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} go_home {speech}.")
    return rb.response

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input,_("Here is the table, press Back to return")))  
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token = "developer-provided-string",
    #                 document = doc,
    #                 datasources = bar 
    #           )
    #         ).response
    #     )
    

# def return_random_noise():
#     x = randrange(0,8)
#     return noises[x], randrange(30 * 1000)
    # if x == 0:
    #     return noise, noise_max_millis
    # if x == 1:
    #     return noise2, noise2_max_millis
    # return noise3, noise2_max_millis

def add_noise_directive(rb):
    try:
        noise,start = return_random_noise()
        rb.add_directive( 
            APLARenderDocumentDirective(
                token= "developer-provided-string",
                document = _load_apl_document("justCrowdNoise.json"),
                datasources = {"text": {"speak": ""},
                    "crowd": {
                        "noise": noise,
                        "start": str(start)
                    }
                }              
            )
          )
    except Exception as ex:
        logger.info("hit exception in add_noise_directive")
        logger.error(ex)        
    
 
def bundesliga_visual(handler_input):
    _ = set_translation(handler_input)
    bun_table = []
    _ = set_translation(handler_input)
    logger.info("at bundesliga table chart")
    s3 = boto3.client("s3")
    resp = s3.get_object(Bucket="bpltables", Key="bundesliga")
    body_str = resp['Body'].read().decode("utf-8")
    x = body_str.split("\n")
    team_index = 0
    bar = copy.deepcopy(foo_table)
    del bar["dataTable"]["properties"]["rows"][18:]
    bar["dataTable"]["back"] = _("Back")
    bar["dataTable"]["properties"]["headings"][1] = _("Team")
    bar["dataTable"]["properties"]["headings"][2] = _("Games")
    bar["dataTable"]["properties"]["headings"][3] = _("wins")
    bar["dataTable"]["properties"]["headings"][4] = _("draws")
    bar["dataTable"]["properties"]["headings"][5] = _("losses")
    bar["dataTable"]["properties"]["headings"][9] = _("Points")
    
    for team in x:
        try:
            #logger.info(f"about to do team {team_index}")
            if team_index < 4:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "green"
            elif team_index < 6:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "blue"
            elif team_index == 15:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "orange"
            elif team_index > 15:
                bar["dataTable"]["properties"]["rows"][team_index]["backgroundColor"] = "red"
                
            one_team = team.split(",")
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][0]["text"] = str(team_index+1)
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][1]["text"] = one_team[0]
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][2]["text"] = str(one_team[1])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][3]["text"] = str(one_team[3])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][4]["text"] = str(one_team[4])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][5]["text"] = str(one_team[5])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][6]["text"] = str(one_team[6])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][7]["text"] = str(one_team[7])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][8]["text"] = str(one_team[8])
            bar["dataTable"]["properties"]["rows"][team_index]["cells"][9]["text"] = str(one_team[2])
            team_index = team_index + 1
            if team_index >= 18:
                break
        except Exception as ex:
            logger.info("hit exception")
            logger.error(ex)        
    doc = _load_apl_document("table.json")
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        try:
            doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
            doc["mainTemplate"]["items"][0]["item"]["items"][1]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
        except Exception as ex:
            logger.info("could not get pixel_height")
            logger.error(ex)
    
    #logger.info("here")        
    rb = handler_input.response_builder
    speech = _("Here is the table, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token = "developer-provided-string",
                    document = doc,
                    datasources = bar 
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} go_home {speech}.")
    return rb.response


   
def championship_visual(handler_input):
    _ = set_translation(handler_input)
    logger.info("at championship table chart")
    load_champ_table()
    logger.info("champ table loaded")
    try:
        championship_table["dataTable"]["back"] = _("Back")
        championship_table["dataTable"]["properties"]["headings"][1] = _("Team")
        championship_table["dataTable"]["properties"]["headings"][2] = _("Games")
        championship_table["dataTable"]["properties"]["headings"][3] = _("wins")
        championship_table["dataTable"]["properties"]["headings"][4] = _("draws")
        championship_table["dataTable"]["properties"]["headings"][5] = _("losses")
        championship_table["dataTable"]["properties"]["headings"][7] = _("Points")

        for index in range(0, 24):
            #logger.info(championship_table["dataTable"]["properties"]["rows"][index] )
            #logger.info('got here')
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][0]["text"] = str(index+1)
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][1]["text"] = short_champ_names.get(champ_table[index][0])
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][2]["text"] = str(champ_table[index][1])
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][3]["text"] = str(champ_table[index][2])
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][4]["text"] = str(champ_table[index][3])
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][5]["text"] = str(champ_table[index][4])
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][6]["text"] = str(champ_table[index][5])
            championship_table["dataTable"]["properties"]["rows"][index]["cells"][7]["text"] = str(champ_table[index][6])

    except Exception as ex:
        logger.info("hit exception")
        logger.error(ex)        

    #logger.info(str(championship_table))
    doc = _load_apl_document("championshiptable.json")
    logger.info(int(handler_input.request_envelope.context.viewport.pixel_height))
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        try:
            # logger.info(doc["mainTemplate"]["items"][0]["item"]["items"][0])
            # logger.info(doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0])
            # logger.info(doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["item"]["fontSize"])
            doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["item"]["fontSize"] = "2vh"
            # logger.info("set header, now set actual data")
            # logger.info(doc["mainTemplate"]["items"][0]["item"]["items"][1]["items"][0]["items"][0]["item"]["fontSize"])
            doc["mainTemplate"]["items"][0]["item"]["items"][1]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
        except Exception as ex:
            logger.info("could not get pixel_height")
            logger.error(ex)
    else:
        logger.info("running on regular device")

    rb = handler_input.response_builder
    speech = _("Here is the table, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token = "developer-provided-string",
                    document = doc,
                    datasources = championship_table 
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} championship {speech}.")
    return rb.response        
    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here is the table, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token = "developer-provided-string",
    #                 document = doc,
    #                 datasources = championship_table 
    #           )
    #         ).response
    #     )
        
    
def load_main_table_data(handler_input):
    _ = set_translation(handler_input)
    reload_main_table_as_needed()
    try:
        #logger.info(str(short_names))
        for index in range(0, 20):
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][0]["text"] = str(index+1)
            #logger.info(f"name:{table_data[index][0].strip()}. short_name {short_names.get(table_data[index][0].strip())}")
            
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][1]["text"] = special_shorten(short_names.get(table_data[index][0].strip(),  table_data[index][0]))
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][2]["text"] = str(table_data[index][1])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][3]["text"] = str(table_data[index][2])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][4]["text"] = str(table_data[index][3])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][5]["text"] = str(table_data[index][4])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][6]["text"] = str(table_data[index][5])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][7]["text"] = str(table_data[index][6])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][8]["text"] = str(table_data[index][7])
            foo_table["dataTable"]["properties"]["rows"][index]["cells"][9]["text"] = str(table_data[index][8])
    except Exception as ex:
        logger.info("hit exception")
        logger.error(ex)        

    #logger.info("about to translate column headers " + _("Points"))
    try:
        foo_table["dataTable"]["back"] = _("Back")
        foo_table["dataTable"]["properties"]["headings"][1] = _("Team")
        foo_table["dataTable"]["properties"]["headings"][2] = _("Games")
        foo_table["dataTable"]["properties"]["headings"][3] = _("wins")
        foo_table["dataTable"]["properties"]["headings"][4] = _("draws")
        foo_table["dataTable"]["properties"]["headings"][5] = _("losses")
        foo_table["dataTable"]["properties"]["headings"][9] = _("Points")
    except Exception as ex:
        logger.info("hit exception")
        logger.error(ex)        


def portrait_table_results(handler_input):
    try:
        # get_progressive_response(handler_input)
        load_main_table_data(handler_input)
        load_fixture_data(handler_input)
        combined_ds = {}
        combined_ds["dataTable"] = foo_table["dataTable"]
        combined_ds["dataTable2"] = results_table["dataTable"]
        
        doc = _load_apl_document("portrait_table.json")
        rb = handler_input.response_builder
        speech = _("Here is the table, press Back to return")
        rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
        rb.add_directive( 
                  APLRenderDocumentDirective(
                    token = "developer-provided-string",
                        document = doc,
                        datasources = combined_ds 
                  )
                )
        add_noise_directive(rb)        
        logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} portrait {speech}.")
        return rb.response        

        # return (
        #     handler_input.response_builder
        #         .speak("Here is the table, press Back to return")
        #         .set_should_end_session(False)          
        #         .add_directive( 
        #           APLRenderDocumentDirective(
        #             token = "developer-provided-string",
        #             document = doc,
        #             datasources = combined_ds 
        #           )
        #         ).response
        #     )
    except Exception as ex:
        logger.info("hit exception")
        logger.error(ex)        
        traceback.print_exc()

    
def table(handler_input):
    _ = set_translation(handler_input)
    #logger.info("at table chart")
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        return portrait_table_results(handler_input)

    load_main_table_data(handler_input)
    
    try:
        doc = _load_apl_document("table.json")
        if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
            logger.info("RUNNING on 15 inch portrait")
            try:
                doc["mainTemplate"]["items"][0]["item"]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
                doc["mainTemplate"]["items"][0]["item"]["items"][1]["items"][0]["items"][0]["item"]["fontSize"] = "1vh"
            except Exception as ex:
                logger.info("could not get pixel_height")
                logger.error(ex)
            #logger.info("TABLE.JSON " + str(doc))
        rb = handler_input.response_builder
        speech = _("Here is the table, press Back to return")
        rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
        rb.add_directive( 
                  APLRenderDocumentDirective(
                    token = "developer-provided-string",
                        document = doc,
                        datasources = foo_table 
                  )
                )
        add_noise_directive(rb)        
        logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} table {speech}.")
        return rb.response        


        # return (
        #     handler_input.response_builder
        #         .speak("Here is the table, press Back to return")
        #         .set_should_end_session(False)          
        #         .add_directive( 
        #           APLRenderDocumentDirective(
        #             token = "developer-provided-string",
        #             document = doc,
        #             datasources = foo_table 
        #           )
        #         ).response
        #     )
    except Exception as ex:
        logger.info("hit exception")
        logger.error(ex)        


def _load_apl_document(file_path):
    with open(file_path) as f:
        return json.load(f)

def get_progressive_response(handler_input):
    # type: (HandlerInput) -> None
    request_id_holder = handler_input.request_envelope.request.request_id
    directive_header = Header(request_id=request_id_holder)
    speech = SpeakDirective(speech="Ok, give me a minute")
    directive_request = SendDirectiveRequest(
        header=directive_header, directive=speech)

    directive_service_client = handler_input.service_client_factory.get_directive_service()
    directive_service_client.enqueue(directive_request)
    time.sleep(5)
    return

                
def goaldifference(handler_input):
    _ = set_translation(handler_input)
    ds = get_goal_difference_url(handler_input)

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are the goal differences, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("url.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} GD {speech}.")
    return rb.response        

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are the goal differences, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )

team_names = [
    "Arsenal" ,          
    "Aston Villa"   ,    
    "Burnley"      ,     
    "Brentford"   ,      
    "Brighton and Hove Albion",
    "Chelsea"   ,        
    "Crystal Palace"  ,  
    "Everton"      ,     
    "Leeds United"  ,    
    "Leicester City",    
    "Liverpool"   ,      
    "Manchester United" ,
    "Manchester City"  , 
    "Newcastle United" , 
    "Norwich City"   ,   
    "Southampton" ,      
    "Tottenham Hotspur" ,
    "Watford"          , 
    "West Ham United"  , 
    "Wolverhampton Wanderers"
]
''' creates a dictionary of number of rank changes by team''' 
def table_rank_changes():
    s3 = boto3.client("s3")
    resp = s3.get_object(Bucket=bucket, Key="line_data")
    body_str = string_data = resp['Body'].read().decode("utf-8")
    n = body_str.split("\n")
    n.pop()
    lines_in_file = len(n)
    week_num = 0
    weeks = []
    for x in range(0,38):
        weeks.append([])
    
    for line in n:
        week_num = 0
        #logger.info(f"line is {line}")
        this_line = line.split(',')
        team = this_line[0]
        team_points = this_line[1:]
        for points in team_points:
            this_tuple = (team,points)
            weeks[week_num].append(this_tuple)
            #logger.info(f"week {week_num} tuple: {this_tuple}")
            week_num += 1

    # logger.info("processed data part one")
    # logger.info(sorted(weeks[0],  key=lambda team: int(team[1])))
    # logger.info(sorted(weeks[1],  key=lambda team: int(team[1])))
    # logger.info(sorted(weeks[2],  key=lambda team: int(team[1])))
    # logger.info(sorted(weeks[3],  key=lambda team: int(team[1])))
    team_rank_changes = {}
    for x in range(2,21):
        week1 = sorted(weeks[x],  key=lambda team: int(team[1]))
        week2 = sorted(weeks[x+1],key=lambda team: int(team[1]))
        num_deltas = 0
        team_rank_change_this_week = {}
        #logger.info(f"{week1} {week2}")
        for w1,w2 in zip(week1,week2):
            if (w1[0] != w2[0]) and (w1[1] != w2[1]):
                num_deltas += 1
                if team_rank_change_this_week.get(w1[0], None) is None:
                    old_team_count = team_rank_changes.get(w1[0], 0)
                    team_rank_changes[w1[0]] = (old_team_count + 1)
                    team_rank_change_this_week[w1[0]] = 1
                    #logger.info(f"{w1[0]} changed rank with {w2[0]}")
                
                if team_rank_change_this_week.get(w2[0], None) is None:
                    old_team_count = team_rank_changes.get(w2[0], 0)
                    team_rank_changes[w2[0]] = (old_team_count + 1)
                    team_rank_change_this_week[w2[0]] = 1
                    #logger.info(f"{w2[0]} changed rank with {w1[0]}")
        #logger.info(f"week {x} had {num_deltas} rank changes")
    return team_rank_changes
    

def get_position_change_url(handler_input):
    _ = set_translation(handler_input)
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    labels = []
    datasets = []
    dict = {
        "type": "bar", 
        "data": {"labels": [], 
                "datasets": [{'data': []}]
        }    
    }
    team_rank_changes = table_rank_changes()
    dict['data']['datasets'][0]['label'] = _("League Position Changes")
    for team in team_names:
        #logger.info(team_rank_changes[team])
        dict['data']['labels'].append(short_names[team])
        dict['data']['datasets'][0]['data'].append(team_rank_changes[team])
    
    qc.config = str(dict).replace('12345', "function(context) {var index = context.dataIndex; var value = context.dataset.data[index];return value < 0 ? 'red' : 'blue';}")

    ret_url = qc.get_short_url()
    #logger.info(f"graphurl: {ret_url}")
    return(ret_url)

    
def rankchanges(handler_input):
    _ = set_translation(handler_input)
    ds = get_position_change_url(handler_input)

   # logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are the table rank changes, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                document = {
                    "type" : "Link",
                    "token" : TOKEN,
                    "src"  : "doc://alexa/apl/documents/GoalDifference"
                },
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} rankchanges {speech}.")
    return rb.response        

    
def get_goal_difference_url(handler_input):
    _ = set_translation(handler_input)
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
    dict["data"]["datasets"][0]["label"] = _("Goal Differences")
    dict["data"]["datasets"][0]["backgroundColor"] = 12345
    dict["data"]["datasets"][0]["borderColor"] = 12345
    dict["data"]["datasets"][0]["borderWidth"] = 1
    qc.config = str(dict).replace('12345', "function(context) {var index = context.dataIndex; var value = context.dataset.data[index];return value < 0 ? 'red' : 'blue';}")
    #logger.info(qc.config)

    ret_url = qc.get_short_url()
    #logger.info(f"graphurl: {ret_url}")
    return(ret_url)
    

def yellow_red(handler_input):
    _ = set_translation(handler_input)
    ds = get_save_percent_url(handler_input,_("Yellow Cards"), _("Red Cards"), _("Cards by Referees"), "yellow_red")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are red and yellow cards by referee, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("url.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
            )
    )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} yellow_red {speech}.")
    return rb.response        

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are red and yellow cards by referee, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )


def attendance(handler_input):
    _ = set_translation(handler_input)
    ds = get_two_stacked_url(handler_input,_("Actual"), _("Capacity"), _("Attendance"), "attendance")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are team attendances, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("advancedCharts.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} attendance {speech}.")
    return rb.response        


    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are team attendances, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )

def in_out_box(handler_input):
    _ = set_translation(handler_input)
    ds = get_two_stacked_url(handler_input,_("Inside Box"), _("Outside Box"), _("Goals"), "in_out_box")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are team goals, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("advancedCharts.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} in_out {speech}.")
    return rb.response        
    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are team goals, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )
        
def var(handler_input):
    _ = set_translation(handler_input)
    ds = get_two_stacked_url(handler_input,_("For"), _("Against"), _("Decisions By Percent For"), "var")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are team VAR decisions, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("advancedCharts.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} var {speech}.")
    return rb.response        
    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are team VAR decisions, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )

def possession(handler_input):
    _ = set_translation(handler_input)
    ds = get_one_stat_url(handler_input,_("Actual"), _("Percent Possession"), "possession")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are team percent possessions, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("advancedCharts.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} possession {speech}.")
    return rb.response        
    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are team percent possessions, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )
        
def corners(handler_input):
    _ = set_translation(handler_input)
    ds = get_one_stat_url(handler_input,_("Corners"), _("Corners"), "corners")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are team corners, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("advancedCharts.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} corners {speech}.")
    return rb.response        

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are team corners, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )
        
def offside(handler_input):
    _ = set_translation(handler_input)
    ds = get_one_stat_url(handler_input,_("Offside"), _("Offside"), "offside")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are team offside, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("advancedCharts.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} offside {speech}.")
    return rb.response        

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are team offside, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )
    
def savepercent(handler_input):
    _ = set_translation(handler_input)
    ds = get_save_percent_url(handler_input,_("Saves"), _("goals allowed"), _("Keeper Saves vs. Goals"), "savepercent")

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are Keeper saves versus goals, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("url.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} savepercent {speech}.")
    return rb.response        

    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are Keeper saves versus goals, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
    #           )
    #         ).response
    #     )
# 

def get_save_percent_url(handler_input, label1, label2, title, filename):
    _ = set_translation(handler_input)
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        qc.height = 700
    if filename == "savepercent":
        names, stat1, stat2 = load_combined_stats(5,"savepercent",1,2,4)
    else:
        names, stat1, stat2 = load_two_stats(5, "yellow_red")

    dict = {
        "type": "bar", 
        "data": {
            "labels": [], 
                "datasets": [
                    {
                        "label": label1,
                        "backgroundColor": 'rgb(75, 192, 192)' if filename == "savepercent" else "yellow",
                        "stack": "Stack 0",
                        "data":[]
                    },
                    {
                        "label": label2,
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
              "text": title
            },
            "scales": {
                "xAxes": [ { "stacked": "true"}],
                "yAxes": [ { "stacked": "true"}],
            }
      }    
    }
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = stat2
    dict["data"]["datasets"][1]["data"] = stat1
    qc.config = str(dict)

    ret_url = qc.get_short_url()
    #logger.info(f"graphurl: {ret_url}")
    return(ret_url)


def get_two_stacked_url(handler_input, label1, label2, title, filename):
    _ = set_translation(handler_input)
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        qc.height = 700
    names, stat1, stat2 = load_two_stats(20, filename)

    dict = {
        "type": "bar", 
        "data": {
            "labels": [], 
                "datasets": [
                    {
                        "label": label1,
                        "backgroundColor": 'rgb(75, 192, 192)',
                        "data":[]
                    },
                    {
                        "label": label2,
                        "backgroundColor": 'rgb(255,99,132)',
                        "data":[]
                    }
                ]
        },
        "options":{
            "responsive": "true",
            "title": {
              "display": "true",
              "text": title
            },
            "scales": {
                "xAxes": [ { "stacked": "true"}],
                "yAxes": [ { "stacked": "true"}],
            }
      }    
    }
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = stat1
    dict["data"]["datasets"][1]["data"] = stat2
    qc.config = str(dict)

    ret_url = qc.get_short_url()
    #logger.info(f"graphurl: {ret_url}")
    return(ret_url)


def get_one_stat_url(handler_input, label1,  title, filename):
    _ = set_translation(handler_input)
    #logger.info("at get_one_stat_url")
    
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        qc.height = 700
    names, stat1, ignore = load_two_stats(20, filename)
    #logger.info("at get_one_stat_url2")

    dict = {
        "type": "bar", 
        "data": {
            "labels": [], 
                "datasets": [
                    {
                        "label": label1,
                        "backgroundColor": 'rgb(75, 192, 192)',
                        "data":[]
                    }
                ]
        },
        "options":{
            "responsive": "true",
            "title": {
              "display": "true",
              "text": title
            }
      }    
    }
    #logger.info("at get_one_stat_url3")
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = stat1
    #dict["data"]["datasets"][1]["data"] = ignore
    qc.config = str(dict)
    #logger.info("at get_one_stat_url4")

    ret_url = qc.get_short_url()
    #logger.info(f"graphurl: {ret_url}")
    return(ret_url)


def goals_shots(handler_input):
    #logger.info("at goals_shots")
    _ = set_translation(handler_input)
    ds = get_goals_shots_url(handler_input)

    #logger.info(ds)
    rb = handler_input.response_builder
    speech = _("Here are goals vs shots, press Back to return")
    rb.speak(wrap_language(handler_input, speech)).set_should_end_session(False)          
    rb.add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("url.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
              )
            )
    add_noise_directive(rb)        
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} goals_shots {speech}.")
    return rb.response        
    # return (
    #     handler_input.response_builder
    #         .speak(wrap_language(handler_input, _("Here are goals vs shots, press Back to return")))
    #         .set_should_end_session(False)          
    #         .add_directive( 
    #           APLRenderDocumentDirective(
    #             token= TOKEN,
    #             document = {
    #                 "type" : "Link",
    #                 "token" : TOKEN,
    #                 "src"  : "doc://alexa/apl/documents/GoalDifference"
    #             },
    #             datasources = {"source": {"url": ds, "back": _("Back")}}
                    
    #           )
    #         ).response
    #     )
    
    
''' goal difference '''


def get_goals_shots_url(handler_input):
    _ = set_translation(handler_input)
    #logger.info("at get_goals_shots_url")
    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        qc.height = 700
    names, goals, shots = load_two_stats(5,"goals_shots")
    #logger.info("after load_two_")
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
    #logger.info("after set dict")
    dict["data"]["labels"] = names
    dict["data"]["datasets"][0]["data"] = goals
    dict["data"]["datasets"][1]["data"] = shots
    qc.config = str(dict)

    ret_url = qc.get_short_url()
    logger.info(f"graphurl: {ret_url}")
    return(ret_url)


def load_group_to_line_chart(session_attr, handler_input, min, max):
    try:
        reset_line_chart(session_attr)
        reload_main_table_as_needed()
        for index in range(min,max):
            session_attr[table_data[index][NAME_INDEX].strip()] = True
    except Exception as ex:
         logger.error(ex)    

def reset_line_chart(session_attr):
    for key in team_colors:
        session_attr[key] = None
    
def get_line_chart_url(session_attr, handler_input):
    _ = set_translation(handler_input)
    #only do this the first time through ....
    if session_attr.get("first_time_graph", None) is None:
        load_group_to_line_chart(session_attr, handler_input,0,6)        
        session_attr["first_time_graph"] = True

    qc = QuickChart()
    qc.width = 500
    qc.height = 300
    if int(handler_input.request_envelope.context.viewport.pixel_height) == 1920:
        logger.info("RUNNING on 15 inch portrait")
        qc.height = 700
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
            #logger.info(f"Team {team} is active, get its points and graph it")
            this_team = form_data.get(team, "not found")
            if team_count < 6:
                team_dict = {'label': short_names[team], 'backgroundColor': rgb, 'borderColor':rgb, 'fill': False, 'data': []}
            else:
                team_dict = {'label': short_names[team], 'backgroundColor': rgb, 'borderColor':rgb, 'borderDash': team_dash.get(team,[]), 'fill': False, 'data': []}
            for point in points:
                team_dict['data'].append(point)
            #logger.info(f"team is {str(team_dict)}")
            dict['data']['datasets'].append(team_dict)
    qc.config = dict
    ret_url = qc.get_short_url()
    #logger.info(f"graphurl: {ret_url}")
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

    #logger.info(ds)
    speech = _("Team points by week, say add or remove team")
    logger.info(f"output_right_directive {handler_input.request_envelope.request.locale} do_line_graph {speech}.")
    return (
        handler_input.response_builder
            .speak(wrap_language(handler_input, speech))
            .set_should_end_session(False)          
            .add_directive( 
              APLRenderDocumentDirective(
                token= TOKEN,
                document = _load_apl_document("RealLineChart.json"),
                datasources = {"source": {"url": ds, "back": _("Back")}}
                    
              )
            ).response
        )


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
            
    #logger.info("highest point is " + str(highest_point))
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
        #logger.info("Add handler")
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
        #logger.info(f"{mode} on a device without a screen, give error")
        response = _("Sorry, adding or removing teams for the graph is only supported on devices with screens.")
        reprompt = _(" What can we tell you about premier league?")
        return (
            handler_input.response_builder
                .ask(reprompt)
                .speak(response + reprompt).response
        )
    prompt = None
    #logger.info("at add_or_delete_team")
    slot = get_slot(handler_input, "plteam")
    logger.info("after get_slot")
    
    if slot.resolutions is not None:    # there is only one slot value
        try:
            dict = slot.resolutions.to_dict()
            #logger.info("Single slot")
            #logger.info(str(dict['resolutions_per_authority'][0]['status']['code']))
            if dict['resolutions_per_authority'][0]['status']['code'] == "ER_SUCCESS_NO_MATCH":
                #logger.info("no matching team found")
                handler_input.response_builder.speak(_("Sorry, I could not find that team, please say add or remove team")).ask("Please try again")
                return handler_input.response_builder.response
            #logger.info("Team name is: " + dict['resolutions_per_authority'][0]["values"][0]["value"]["name"])
            team = dict['resolutions_per_authority'][0]["values"][0]["value"]["name"]
            session_attr = handler_input.attributes_manager.session_attributes
            if mode == "add":
                session_attr[team] = True
                #prompt = "added {} to the graph".format(team)
            else:
                session_attr.pop(team, "not found ")
                #logger.info(f"removed {team} from the session and its still there?: {team_in_chart(session_attr,team)}")
                #prompt = "removed {} from the graph".format(team)
            handler_input.attributes_manager.session_attributes = session_attr
        except Exception as ex:
            logger.info("exception getting slot")
            logger.info(ex)
      
        return((do_line_graph(handler_input)))   #(do_line_graph(handler_input))

    else:  # there are multiple slot values
        #logger.info("Multiple slot")
        session_attr = handler_input.attributes_manager.session_attributes
        prompt = mode + "ed "
        if slot.slot_value is not None:
            for value in slot.slot_value.values:
                #logger.info("Team Name: " + str(value.resolutions.resolutions_per_authority[0].values[0].value.name))
                team = str(value.resolutions.resolutions_per_authority[0].values[0].value.name)
                if mode == "add":
                    session_attr[team] = True
                    logger.info(f"added {team} to the session")
                    prompt += team
                else:
                    session_attr.pop(team, "not found 2")
                    logger.info(f"removed {team} to the session and its still there?: {team_in_chart(session_attr,team)}")
                    prompt += team
        else:
            #logger.info("no matching team found")
            handler_input.response_builder.speak(_("Sorry, I could not understand the team name, please say add or remove team")).ask("Please try again")
            return handler_input.response_builder.response
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
short_champ_names = {
"Bournemouth" : "Bournemouth",
"Fulham" : "Fulham",
"West Bromwich Albion" : "West Brom",
"Coventry City" : "Coventry",
"Stoke City" : "Stoke",
"Queens Park Rangers" : "QPR",
"Blackburn Rovers" : "Blackburn",
"Huddersfield Town" : "Huddersfield",
"Millwall" : "Millwall",
"Blackpool" : "Blockpool",
"Luton Town" : "Luton",
"Swansea City" : "Swansea",
"Nottingham Forest" : "Forest",
"Middlesbrough" : "Middlebrough",
"Birmingham City" : "Birminghm",
"Reading" : "Reading",
"Preston North End" : "Preston",
"Sheffield United" : "Sheffield",
"Bristol City" : "Bristol",
"Cardiff City" : "Cardiff",
"Peterborough United" : "Peterborough",
"Hull City" : "Hull",
"Barnsley" : "Barneley",
"Derby County" : "Derby"    
}