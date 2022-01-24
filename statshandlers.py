from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name, get_intent_name, get_slot, get_slot_value
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective as APLRenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apla import RenderDocumentDirective as APLARenderDocumentDirective
from ask_sdk_core.utils import get_supported_interfaces
from ask_sdk_core.utils.viewport import get_viewport_profile
from ask_sdk_core.utils.request_util import is_new_session
from ask_sdk_model.ui import SimpleCard, StandardCard, Image
from ask_sdk_model import Response
import shared
from shared import extra_cmd_prompts, doc, noise, noise2, noise3, noise_max_millis, noise2_max_millis, noise3_max_millis
import logging
import random
from random import randrange
import re
import boto3
import json
import requests
from shared import extra_cmd_prompts, doc, noise, noise2, noise3, noise_max_millis, results_table 
from shared import noise2_max_millis, noise3_max_millis, datasources2, datasourcessp, test_speach_data, noise_data, teamsdatasource
from datetime import datetime
import spanishnumber
#import isp
#from isp import ds2_advanced_or_not
#from multimedia import yellow_red
import gettext
import traceback

lang_translations_en = gettext.translation('base', localedir='locales', languages=['en'])
lang_translations_en.install()
lang_translations_sp = gettext.translation('base', localedir='locales', languages=['es'])
lang_translations_sp.install()
_ = lang_translations_sp.gettext

table_data = []
table_index = 0
NAME_INDEX = 0
PLAYED_INDEX = 1
WINS_INDEX = 2
DRAWS_INDEX = 3
LOSSES_INDEX = 4
GOALS_FOR_INDEX = 5
GOALS_AGAINST_INDEX = 6
GOAL_DIFF_INDEX = 7
POINTS_INDEX = 8

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

'''
wrap_language
is_spanish
set_translation
GoalsHandler
goal_hander
ListTeamNamesHandler
CleanSheetsHandler
cleansheets_handler
FoulsHandler
foul_handler
output_right_directive
YellowCardHandler
yellowcard_handler
RedCardHandler
redcard_handler
TouchesHandler
touches_handler
TacklesHandler
tackles_handler
RefereesHandler
referees_handler
ResultsHandler
results_handler
FixturesHandler
fixtures_handler
TableHandler
table_handler
RelegationHandler
relegation_handler
build_team_speech
team_handler
build_relegation_fragment
build_table_fragment
say_place
reload_main_table_as_needed
load_main_table
'''

def set_session_start_time(handler_input):
    try:
        if is_new_session(handler_input):
            logger.info("at set_session_start_time")
            session_attr = handler_input.attributes_manager.session_attributes
            session_attr["session_start_time"] = datetime.timestamp(datetime.now())
            handler_input.attributes_manager.session_attributes = session_attr
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()
        
    
def wrap_language(handler_input, text):
    spanish_prefix = "<lang xml:lang='es-US'><voice name='Miguel'>"
    spanish_suffix = "</voice></lang>"
    logger.info(f"wrap in spanish:{is_spanish(handler_input)}")
    return spanish_prefix+text+spanish_suffix if is_spanish(handler_input) == True else text


def is_spanish(handler_input):
    loc = handler_input.request_envelope.request.locale
    return loc == "es-US" or loc == "es-ES" or loc == "es-MX"

''' 
CloudWatch metrics on locale, grouping all the Spanish variants together 
Two metrics are emitted, one just for locale and another for locale/AV_type
It also emits a metric for with or without a screen
'''
def emit_locale_metric(handler_input):
    loc = handler_input.request_envelope.request.locale
    cw = boto3.client("cloudwatch")
    if has_screen(handler_input):
        cw.put_metric_data(
            Namespace='PremierLeague',
            MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
        )
    else:
        cw.put_metric_data(
            Namespace='PremierLeague',
            MetricData=[{'MetricName': 'InvocationsWithOutScreen','Timestamp': datetime.now(),'Value': 1,},]
        ) 
        
    if is_spanish(handler_input):
        loc = "ES"
    cw.put_metric_data(
                Namespace='PremierLeague',
                MetricData=[
                    {
                        'MetricName': 'locale',
                        'Dimensions': [{ 'Name': 'locale','Value': loc},],
                        'Value': 1,
                        'Unit': 'Count'
                    },
                ]
            )
    device_type = "-Show" if has_screen(handler_input) else "-Dot"
    cw.put_metric_data(
                Namespace='PremierLeague',
                MetricData=[
                    {
                        'MetricName': 'localeAV',
                        'Dimensions': [{ 'Name': 'localeAV','Value': loc+device_type},],
                        'Value': 1,
                        'Unit': 'Count'
                    },
                ]
            )
        


def set_translation(handler_input):
    #logger.info("at set_translation {}".format(handler_input.request_envelope.request.locale))
    if is_spanish(handler_input):
        _ = lang_translations_sp.gettext
    else:        
        _ = lang_translations_en.gettext
        
    #logger.info("returning _ after set_translation {}".format(_))
    return _
    
def has_screen(handler_input):
    return (get_supported_interfaces(handler_input).alexa_presentation_apl is not None)

    
class GoalsHandler(AbstractRequestHandler):
    """Handler for GoldenBootIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("GoldenBootIntent")(handler_input))


    def handle(self, handler_input):
        logger.info("In GoalsHandler")
        return goal_hander(handler_input)
        
def goal_hander(handler_input):
    try:
        _ = set_translation(handler_input)
        if "goals" in extra_cmd_prompts:
            del extra_cmd_prompts["goals"]
        goal_phrases = [_("the players with the most goals are,"),_("the highest scorers are, "),_("the top scorers are")]
        intro = random_phrase(0,2, goal_phrases)
        
        speech, card_text = load_stats(5, "goldenboot", _(", with "), _(" has "), "  ", 1, 2, 4)
        speech = intro + speech + ',' + random_prompt(handler_input)
        
        image_url = "https://duy7y3nglgmh.cloudfront.net/Depositphotos_goal.jpg"
        logger.info("about to call output_right_directive")
        return output_right_directive(handler_input, speech, image_url, noise, noise_max_millis)
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()
    

class ListTeamNamesHandler(AbstractRequestHandler):
    """Handler for ListTeamNamesIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle ListTeamNamesHandler")
        return (is_intent_name("ListTeamNamesIntent")(handler_input))

    def handle(self, handler_input):
        _ = set_translation(handler_input)
        logger.info("In ListTeamNamesHandler")
        team_name_phrases = [_("We recognize the following team names"),_("These are the teams in the best league in the world"),_("The best teams are")]
        intro = random_phrase(0,2, team_name_phrases)
        speech  = ',,Arsenal, Aston Villa, Brentford, Brighton and Hove Albion, Burnley, Chelsea, Crystal Palace,'
        speech += 'Everton, Leeds, Leicester City, Liverpool, Manchester City, Manchester United, Newcastle United,'
        speech += 'Norwich City, Southampton, Tottenham Hotspur, Watford, West Ham United and Wolverhamton Wandereres,,'
        speech += _('You can also refer to teams by their nicknames like gunners or toffees')
        speech = intro + speech
        image_url = "https://duy7y3nglgmh.cloudfront.net/Depositphotos_touches.jpg"
        
        return output_right_directive(handler_input, speech, image_url, noise, noise_max_millis)


class CleanSheetsHandler(AbstractRequestHandler):
    """Handler for CleanSheetsIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle CleanSheetsHandler")
        return (is_intent_name("CleanSheetsIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In CleanSheetsHandler")
        return(cleansheets_handler(handler_input))
        
def cleansheets_handler(handler_input):
    logger.info("at actual cleansheets_handler")
    _ = set_translation(handler_input)
    if "cleansheets" in extra_cmd_prompts:
        del extra_cmd_prompts["cleansheets"]
    clean_phrases = [_("the goalkeepers with the most clean sheets are,"),_("the most clean sheets go to, "), _("the keepers with the most clean sheets are")]
    intro = random_phrase(0,2, clean_phrases)
    
    speech, card_text = load_stats(5, "cleansheets", _(", with "), _(" has "), "  ", 1, 2, 4)
    speech = intro + speech + ',' + random_prompt(handler_input)
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/Depositphotos_keeper.jpg"
    return output_right_directive(handler_input, speech, image_url, noise3, noise3_max_millis)


class FoulsHandler(AbstractRequestHandler):
    """Handler for FoulsIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle FoulsHandler")
        return (is_intent_name("FoulsIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In FoulsHandler")
        return(foul_handler(handler_input))
        
def foul_handler(handler_input):
    _ = set_translation(handler_input)
    if "fouls" in extra_cmd_prompts:
        del extra_cmd_prompts["fouls"]
    foul_phrases = [_("the players with the most fouls are,"),_("the most fouls were committed by, "),_("the top foulers were,")]
    intro = random_phrase(0,2, foul_phrases)
    
    speech, card_text = load_stats(5, "fouls", _(", with "), _(" has "), "  ", 1, 2, 4)
    speech = intro + speech + ',' + random_prompt(handler_input)
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/Depositphotos_fouls.jpg"
    return output_right_directive(handler_input, speech, image_url, noise3, noise3_max_millis)


def output_right_directive(handler_input, the_text, image_url, noise, noise_max):
    _ = set_translation(handler_input)
    logger.info("at output_right_directive")
    set_session_start_time(handler_input)
        
    emit_locale_metric(handler_input)
    session_attr = handler_input.attributes_manager.session_attributes
    already_displayed_screen = session_attr.get("screen_displayed", False)
    noise_start = str(randrange(0, noise_max))
    the_text = wrap_language(handler_input, the_text)
    
    if get_supported_interfaces(handler_input).alexa_presentation_apl is not None and not already_displayed_screen:
        session_attr["radioButtonText"] = "Form"
        handler_input.attributes_manager.session_attributes = session_attr
        this_profile = str(get_viewport_profile(handler_input.request_envelope))
        item_heights = {"ViewportProfile.HUB_LANDSCAPE_SMALL": "75%", "ViewportProfile.HUB_LANDSCAPE_MEDIUM": "65%", "ViewportProfile.HUB_LANDSCAPE_LARGE": "55%"}
        this_height = item_heights.get(this_profile, "")
        datasources2["gridListData"]["listItemHeight"] = this_height
        # if is_spanish(handler_input):
        #     datasources2["gridListData"]["title"] = "Puedes preguntar sobre"

        session_attr["screen_displayed"] = True
        handler_input.attributes_manager.session_attributes = session_attr

        logger.info(f"output_right_directive visual {the_text}")
        return (handler_input.response_builder.speak(the_text).set_should_end_session(False)          
                .add_directive( APLRenderDocumentDirective(
                    token= "TOKEN",
                    document = {"type" : "Link","token" : "TOKEN","src"  : "doc://alexa/apl/documents/GridList"},
                    datasources = datasourcessp if is_spanish(handler_input) else datasources2)).response)
    elif get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
        logger.info(f"output_right_directive audio {the_text}, {image_url}, {noise}, {noise_max} {noise_start}.")
        return(handler_input.response_builder.ask(the_text).add_directive(  
              APLARenderDocumentDirective(
                token= "tok",
                document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": the_text},"crowd": {"noise": noise,"start": noise_start}
                }
            )).response)
    else:
        card = StandardCard(title=_("Premier League"), text=strip_emotions(the_text), image=Image(small_image_url=image_url, large_image_url=image_url))
        logger.info("Outputing StandardCard")
        logger.info(f"output_right_directive audio {the_text}, {image_url}, {noise}, {noise_max} {noise_start}.")
        return(handler_input.response_builder.set_card(card).ask(the_text).add_directive(
              APLARenderDocumentDirective(
                token= "tok",
                document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": the_text},"crowd": {"noise": noise,"start": noise_start}
                }
            )).response)
        


class YellowCardHandler(AbstractRequestHandler):
    """Handler for YellowCardIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle YellowCardHandler")
        return (is_intent_name("YellowCardIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In YellowCardHandler")
        return(yellowcard_handler(handler_input))
        
def yellowcard_handler(handler_input):
    _ = set_translation(handler_input)
    if "yellowcards" in extra_cmd_prompts:
        del extra_cmd_prompts["yellowcards"]
    yellow_phrases = [_("the players with the most yellow cards are,"), _("the most cautioned players are, "), _("the most booked players are,")]
    intro = random_phrase(0,2, yellow_phrases)
    
    speech, card_text = load_stats(5, "yellowcards", _(", with "), _(" has "), "  ", 1, 2, 4)
    speech = intro + speech + ',' + random_prompt(handler_input)
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/yellowcard.png"
    return output_right_directive(handler_input, speech, image_url, noise3, noise3_max_millis)


class RedCardHandler(AbstractRequestHandler):
    """Handler for RedCardIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle RedCardHandler")
        return (is_intent_name("RedCardIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In RedCardHandler")
        return(redcard_handler(handler_input))
        
def redcard_handler(handler_input):
    _ = set_translation(handler_input)
    if "redcards" in extra_cmd_prompts:
        del extra_cmd_prompts["redcards"]
    red_phrases = [_("the players with the most red cards are,"),_("the most ejected players are, "),_("the players leaving their teams playing short the most are, ")]
    intro = random_phrase(0,2, red_phrases)
    
    speech, card_text = load_stats(5, "redcards", _(", with "), _(" has "), "  ", 1, 2, 4)
    speech = intro + speech + ',' + random_prompt(handler_input);
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/redcard.png"
    return output_right_directive(handler_input, speech, image_url, noise, noise_max_millis)


class TouchesHandler(AbstractRequestHandler):
    """Handler for TouchesIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("TouchesIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In TouchesHandler")
        return(touches_handler(handler_input))
        
def touches_handler(handler_input):
    _ = set_translation(handler_input)
    if "touches" in extra_cmd_prompts:
        del extra_cmd_prompts["touches"]
    touch_phrases = [_("the players with the most touches are,"),_("the players touching the ball the most are, "), _("the most touches go to, ")]
    intro = random_phrase(0,2, touch_phrases)
    
    speech, card_text = load_stats(5, "touches", _(", with "), _(" has "), "  ", 1, 2, 4)
    speech = intro + speech + ',' + random_prompt(handler_input)
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/Depositphotos_touches.jpg"
    return output_right_directive(handler_input, speech, image_url, noise, noise_max_millis)


class TacklesHandler(AbstractRequestHandler):
    """Handler for TacklesIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("TacklesIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In TacklesHandler")
        return(tackles_handler(handler_input))
        
def tackles_handler(handler_input):    
    _ = set_translation(handler_input)
    if "tackles" in extra_cmd_prompts:
        del extra_cmd_prompts["tackles"]
    tackles_phrases = [_("the players with the most tackles are,"),_("the players tackling the most are, "), _("the most tackles go to, ")]
    intro = random_phrase(0,2, tackles_phrases)
    
    logger.info( f"TACKLES LANG: spanish: {is_spanish(handler_input)} locale: {handler_input.request_envelope.request.locale}")
    
    speech, card_text = load_stats(5, "tackles", _(", with "), _(" has "), "  ", 1, 2, 4)
    speech = intro + speech + ',' + random_prompt(handler_input)
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/tackles.png"
    return output_right_directive(handler_input, speech, image_url, noise2, noise2_max_millis)


class RefereesHandler(AbstractRequestHandler):
    """Handler for RefereesIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("RefereesIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In RefereesHandler")
        return(referees_handler(handler_input))
        
def referees_handler(handler_input):
    _ = set_translation(handler_input)
    if "referees" in extra_cmd_prompts:
        del extra_cmd_prompts["referees"]

    referees_phrases = [_("the most used referees are, "),_("the referees who've called the most games are, "),_("the referees in charge of the most games are,  ")]
    intro = random_phrase(0,2, referees_phrases)
    
    speech, card_text = load_stats(5, "referees", " ", _(" yellow cards and "), _(" red cards"), 0, 3, 2)
    speech = intro + speech + ','
    speech = speech + random_prompt(handler_input)
    
    image_url = "https://duy7y3nglgmh.cloudfront.net/Depositphotos_referee.jpg"
    return output_right_directive(handler_input, speech, image_url, noise2, noise2_max_millis)


class ResultsHandler(AbstractRequestHandler):
    """Handler for ResultsIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle ResultsHandler")
        return (is_intent_name("ResultsIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In ResultsHandler")
        return(results_handler(handler_input))

        
def results_handler(handler_input):    
    _ = set_translation(handler_input)
    if "results" in extra_cmd_prompts:
        del extra_cmd_prompts["results"]
    result_phrases = [_("the results for the recent match week were, "),_("last weeks results were "),_("last week saw  ")]
    intro = random_phrase(0,2, result_phrases)
    
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr["which_list"] = "results"
    session_attr["results_index"] = 5
    handler_input.attributes_manager.session_attributes = session_attr
    
    speech, card_text = load_stats_ng(handler_input, 5, "prevWeekFixtures", "  ", "  ", "  ", 0, 2, 1, "")
    if is_spanish(handler_input):
        card_text = card_text.replace("beat", "vencer").replace("lost to", "perdió ante").replace("drew", "Empate").replace(" to ", " por ")
        str1 = speech.replace("beat", "vencer").replace("lost to", "perdió ante").replace("drew", "Empate").replace(" to ", " por ")
        speech = str1
    speech = intro + speech + ',' + _('Would you like to hear more?')
    image_url = "https://duy7y3nglgmh.cloudfront.net/tackles.png"
    
    return output_right_directive(handler_input, speech, image_url, noise2, noise2_max_millis)



class FixturesHandler(AbstractRequestHandler):
    """Handler for FixturesIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("FixturesIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In FixturesHandler")
        return(fixtures_handler(handler_input))
        
def fixtures_handler(handler_input):    
    _ = set_translation(handler_input)
    if "fixtures" in extra_cmd_prompts:
        del extra_cmd_prompts["fixtures"]
    fixture_phrases = [_("the fixtures for the current upcoming match week are,"), _("next week we'll see"), _("the next games are,")]
    intro = random_phrase(0,2, fixture_phrases)
    set_time_zone(handler_input)        

    session_attr = handler_input.attributes_manager.session_attributes
    session_attr["which_list"] = "fixtures"
    session_attr["fixture_index"] = 5
    handler_input.attributes_manager.session_attributes = session_attr
    
    speech, card_text = load_stats_ng(handler_input, 5, "fixtures2", _(" versus "), _(" at "), "  ", 0, 2, 1, "")
    speech = day_of_week_trans(handler_input,speech)
    speech = month_trans(handler_input,speech)
    if not is_spanish(handler_input):
        speech = speech.replace("oh clock", "")
    speech = intro + speech + _('Would you like to hear more?')
    image_url = "https://duy7y3nglgmh.cloudfront.net/tackles.png"
    logger.info("saying fixture " + speech)
    return output_right_directive(handler_input, speech, image_url, noise2, noise2_max_millis)


def month_trans(handler_input, src_text):
    logger.info("translating " + src_text + ".")
    months = [("January","Enero"),("February","Enero"), ("March","Marzo"), 
            ("April","Abril"), ("May","Mayo"), ("June","Junio"), ("July","Julio"), 
            ("August","Agosto"), ("September","Septiembre"), ("October","Octubre"), ("November","Noviembre"), ("December","Diciembre")]
    if is_spanish(handler_input):
        for month in months:
            src_text = src_text.replace(month[0], month[1])
    logger.info("got " + src_text + ".")
    return src_text
    
    
def day_of_week_trans(handler_input, src_text):
    if is_spanish(handler_input):
        for day in ["Monday", "Tuesday"]:
            src_text = src_text.replace("Monday","Lunes").replace("Tuesday","Martes").replace("Wednesday", "Miércoles").replace("Thursday", "Jueves").replace("Friday","Viernes").replace("Saturday", "Sábado").replace("Sunday","Domingo")
    return src_text

class TableHandler(AbstractRequestHandler):
    """Handler for TableIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("TableIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In TableHandler")
        return(table_handler(handler_input))
        
def table_handler(handler_input):    
    _ = set_translation(handler_input)
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr["table_index"] = 5
    session_attr["which_list"] = "table"
    handler_input.attributes_manager.session_attributes = session_attr
    
    table_index = 0
    speech = _('The first five teams in the table are ') + build_table_fragment(table_index, handler_input)
    card_text = strip_emotions(speech)
    speech = speech + _('Would you like to hear more?')
    image_url = "https://duy7y3nglgmh.cloudfront.net/tackles.png"
    
    return output_right_directive(handler_input, speech, image_url, noise, noise_max_millis)


class RelegationHandler(AbstractRequestHandler):
    """Handler for RelegationIntent."""

    def can_handle(self, handler_input):
        return (is_intent_name("RelegationIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In RelegationHandler")
        return(relegation_handler(handler_input))

        
def relegation_handler(handler_input):    
    _ = set_translation(handler_input)
    if "relegation" in extra_cmd_prompts:
        del extra_cmd_prompts["relegation"]
    relegation_phrases = [_("in the relegation zone "),_("facing relegation"),_("in danger ")];
    thisPhrase = random_phrase(0,2, relegation_phrases);
    speech = _("the teams currently ") + thisPhrase + _(" are ") + build_relegation_fragment(handler_input);
    speech = speech + ',' + random_prompt(handler_input)
    image_url = "https://duy7y3nglgmh.cloudfront.net/tackles.png"
    
    return output_right_directive(handler_input, speech, image_url, noise, noise_max_millis)


def build_team_speech(handler_input, this_team_index, team_name):
    _ = set_translation(handler_input)
    logger.info(f"building team speak for {team_name} at index {this_team_index}")
    speech = _("You asked about ") + team_name + _(", their form is ")
    form = say_place(this_team_index + 1, handler_input) + _(" with ") + pluralize(handler_input,table_data[this_team_index][WINS_INDEX], _("win"), 's') + ", "
    form = form + pluralize(handler_input,table_data[this_team_index][DRAWS_INDEX], _(" draw"), 's') + ", "
    form = form + pluralize(handler_input,table_data[this_team_index][LOSSES_INDEX], _(" loss"), 'es') + ", "
    form = form + pluralize(handler_input,table_data[this_team_index][GOALS_FOR_INDEX], _(" goal"), 's') + _(" scored, ")
    form = form + pluralize(handler_input,table_data[this_team_index][GOALS_AGAINST_INDEX], _(" goal"), 's') + _(" allowed, ")
    form = form + _(" for a goal difference of ") + table_data[this_team_index][GOAL_DIFF_INDEX] + _(", and ")
    form = form + pluralize(handler_input,table_data[this_team_index][POINTS_INDEX], _(" point"), 's') + ", "
    form = get_excitement_prefix(this_team_index, handler_input) + form + get_excitement_suffix(handler_input)
    card_text = strip_emotions(speech + form)
    new_intent = _(", you can also ask for fixtures or results for {}").format(team_name)
    speech = speech + form + new_intent
    return (card_text, speech)
    
    
def team_handler(handler_input, team_id):  
    _ = set_translation(handler_input)
    logger.info("at team_handler")
    card_text = ""
    reload_main_table_as_needed()
    if team_id is not None:
        logger.info("found team")
        this_team_index = find_team_index(team_id)
        card_text, speech = build_team_speech(handler_input, this_team_index, team_id)
    else:    
        slot = get_slot(handler_input, "plteam")
        if slot.resolutions is None:
            logger.info("no matching team found")
            handler_input.response_builder.speak(_("Sorry, I could not find that team, please say a premier league team")).ask(_("Please try again"))
            return handler_input.response_builder.response

        dict = slot.resolutions.to_dict()
        success = dict['resolutions_per_authority'][0]["status"]["code"]
        if success == 'ER_SUCCESS_MATCH':
            team_id = dict['resolutions_per_authority'][0]["values"][0]["value"]["id"]
            team_name = dict['resolutions_per_authority'][0]["values"][0]["value"]["name"]
            logger.info("found team {} {}".format(team_id, team_name))
            if team_id == 'Southhampton':
                team_id = 'Southampton'
    
            this_team_index = find_team_index(team_id)
            if this_team_index == -1:
                logger.info("could not find team")
                speech = _("could not find team")
                card_text = speech
            else:
                card_text, speech = build_team_speech(handler_input, this_team_index, team_name)
        else:
            logger.info("could not find team")
            err_msg = _("could not find team with that name, please try again or ask us for a list of team names")
            team_id = None
            logger.info(err_msg)
            speech = err_msg
        
    team_logos = ["Arsenal","AstonVilla","Brentford","BrightonAndHoveAlbion","Burnley", "Chelsea","CrystalPalace","Everton","LeedsUnited","LeicesterCity","Liverpool","ManchesterUnited","ManchesterCity","NewcastleUnited","NorwichCity","Southhampton","TottenhamHotspur","Watford","WestHamUnited","WolverhamptonWanderers" ]
    if team_id is not None:
        logger.info("building team response " + speech)
        #image_url = "https://bplskillimages.s3.amazonaws.com/" + team_id + ".png"
        image_url = "https://duy7y3nglgmh.cloudfront.net/" + team_id + ".png"
    else:    
        logger.info("built simple card")
    logger.info(f"team_handler speech {speech}")
    return output_right_directive(handler_input, speech, "https://duy7y3nglgmh.cloudfront.net/football_pitch.png", noise, noise_max_millis)


def build_relegation_fragment(handler_input):
    logger.info("at build_relegation_fragment")
    _ = set_translation(handler_input)
    reload_main_table_as_needed()
    logger.info("there are now {} teams in the table_data".format(len(table_data)))
    relegation_fragment = ""
    for index in range(17,20):
        logger.info("index {}".format(index))
        logger.info("name {}".format(table_data[index][NAME_INDEX]))
        logger.info("points {}".format(pluralize(handler_input,table_data[index][POINTS_INDEX], 'point', 's')))
        
        relegation_fragment = relegation_fragment + say_place(index+1, handler_input) + " " + table_data[index][NAME_INDEX] + _(" with ") + pluralize(handler_input,table_data[index][POINTS_INDEX], _(' point'), 's') + ', '
    return '<amazon:emotion name="disappointed" intensity="high">' + relegation_fragment + '</amazon:emotion>'


def ordinal(num):
    ordinals =  [
        "primero",
        "segundo",
        "tercero",
        "cuarto",
        "quinto",
        "sexto",
        "séptimo",
        "octavo",
        "noveno",
        "décimo",
        "undécimo",
        "duodécimo",
        "decimotercero",
        "decimocuarto",
        "decimoquinto",
        "decimosexto",
        "decimoséptimo",
        "decimoctavo",
        "decimonoveno",
        "vigésimo",
        "vigésimo primero",
        "vigésimo segundo",
        "vigésimo tercero",
        "vigésimo cuarto"
        ]
    return ordinals[num]
    
def build_spanish_table_fragment(table_index, handler_input):
    _ = set_translation(handler_input)
    table_fragment = " "
    reload_main_table_as_needed()
    for index in range(table_index, table_index+5):
        #table_fragment = table_fragment + say_place(index+1, handler_input) + " " + table_data[index][NAME_INDEX] + _(" with ") + pluralize(handler_input,table_data[index][POINTS_INDEX], _(' point'), 's') + ', '
        table_fragment = table_fragment + table_data[index][NAME_INDEX] + " que está " + ordinal(index) + " con " + table_data[index][POINTS_INDEX] + ' puntos, '

    returned_str = get_excitement_prefix(table_index, handler_input) + table_fragment + get_excitement_suffix(handler_input)
    table_index = table_index + 5
    return returned_str


def build_table_fragment(table_index, handler_input):
    _ = set_translation(handler_input)
    if is_spanish(handler_input):
        return build_spanish_table_fragment(table_index, handler_input)
    table_fragment = ""
    reload_main_table_as_needed()
    for index in range(table_index, table_index+5):
        table_fragment = table_fragment + say_place(index+1, handler_input) + " " + table_data[index][NAME_INDEX] + _(" with ") + pluralize(handler_input,table_data[index][POINTS_INDEX], _(' point'), 's') + ', '

    returned_str = get_excitement_prefix(table_index,handler_input) + table_fragment + get_excitement_suffix(handler_input)
    table_index = table_index + 5
    return returned_str


def say_place(table_index, handler_input):
    _ = set_translation(handler_input)
    if table_index == 1:
        return _("first place")
    elif table_index == 2:
        return _("second place")
    elif table_index == 3:
        return _("third place")
    else:
        place = "th place" if is_spanish(handler_input)==False else " poner"
        return str(table_index) + place

    
def reload_main_table_as_needed():
    if len(table_data) == 0:
        logger.info("needed to reload main table")
        load_main_table()
    else:
        logger.info("did not need to load main table")

        
def load_main_table():
    s3 = boto3.client("s3")
    logger.info("about to open main table")
    resp = s3.get_object(Bucket="bpltables", Key="liveMainTable")
    logger.info("back from open main table")
    body_str = resp['Body'].read().decode("utf-8")
    logger.info("converted streaming_body to string")
    x = body_str.split("\n")
    team_index = 0
    #table_data.clear()
    #table_data = []

    for team in x:
        one_team = team.split(",")
        table_data.append(one_team)
        team_index = team_index + 1
        if team_index > 19:
            break
    table_index = 0
    logger.info("loaded {} teams into table_data".format(len(table_data)))
    

champ_table = []

def load_champ_table():
    s3 = boto3.client("s3")
    logger.info("about to open chap table")
    resp = s3.get_object(Bucket="bpltables", Key="championship_table")
    logger.info("back from open champ table")
    body_str = resp['Body'].read().decode("utf-8")
    logger.info("converted streaming_body to string")
    x = body_str.split("\n")
    team_index = 0

    for team in x:
        one_team = team.split(",")
        champ_table.append(one_team)
        team_index = team_index + 1
        if team_index > 23:
            break
    table_index = 0
    logger.info("loaded {} teams into champ_table".format(len(champ_table)))


def random_phrase(low, high, phrases):
    return phrases[randrange(low, high)];


def random_prompt(handler_input):
    _ = set_translation(handler_input)
    variedPrompts = [_("Say get table, or say a team name "), _("Ask about the table or a team"), _("What can we tell you about Premier League  "), _("We can tell you about teams or the table")]
    return variedPrompts[randrange(0, 3)] + suggest(handler_input);
  
    
def pluralize(handler_input,count, noun, ess):
    if int(count) == 1:
        return count + " " + noun
    else:
        return count + " " + noun + ess
        

def load_suggestions(handler_input):
    _ = set_translation(handler_input)
    extra_cmd_prompts["touches"]      = _(". you can also ask about touches")
    extra_cmd_prompts["fouls"]        = _(". you can also ask about fouls")
    extra_cmd_prompts["tackles"]      = _(". you can also ask about tackles")
    extra_cmd_prompts["stadiums"]     = _(". you can also ask about Premier League stadiums by name")
    extra_cmd_prompts["referees"]     = _(". you can also ask about referees")
    extra_cmd_prompts["fixtures"]     = _(". you can also ask about fixtures")
    extra_cmd_prompts["results"]      = _(". you can also ask about last weeks results")
    extra_cmd_prompts["teamfixtures"] = _(". you can also ask about fixtures for a team")
    extra_cmd_prompts["teamresults"]  = _(". you can also ask about results for a team")
    extra_cmd_prompts["relegation"]   = _(". you can also ask about relegation")
    extra_cmd_prompts["redcards"]     = _(". you can also say red cards")
    extra_cmd_prompts["yellowcards"]  = _(". you can also say yellow card")
    extra_cmd_prompts["cleansheets"]  = _(". you can also ask about clean sheets")
    extra_cmd_prompts["goals"]        = _(". you can also ask about goals")


def suggest(handler_input):
    session_attr = handler_input.attributes_manager.session_attributes
    if session_attr.get("screen_displayed", False) == True:
        return ""
    suggestions_left = len(extra_cmd_prompts)
    logger.info("There are {} suggestions remaining".format(suggestions_left))
    sugs = " "
    if suggestions_left > 0:
        key,value = random.choice(list(extra_cmd_prompts.items()))
        #del extra_cmd_prompts[key]
        logger.info("suggesting " + value)
        return value
    else:
        load_suggestions(handler_input)    
    return ""


def strip_emotions(str):
    #logger.info(f"strip_emotions {str}")
    try:
        # index = str.index("<")
        # index2 = str.index(">")
        # str2 = str[:index] + str[index2+1:]
        # return str2.replace("</amazon:emotion>","")
        index = 1
        while index > -1:
            index = str.find("<")
            index2 = str.find(">") + 1
            str = str.replace(str[index:index2],"")
        #logger.info(f"strip_emotions {str}")
        return str
    except:
        return str

def get_excitement_prefix(index,handler_input):
    ''' speak with excitement or disappointment but with some randomness '''

    if is_spanish(handler_input):   # emotions only supported for English voices 
        return ""
    high_or_medium = "high" if randrange(0,2)==0 else "medium"
    medium_or_low = "medium" if randrange(0,2)==0 else "low"
    
    if index < 5:
        return '<amazon:emotion name="excited" intensity="{}">'.format(high_or_medium)
    elif index < 10:
        return '<amazon:emotion name="excited" intensity="{}">'.format(medium_or_low)
    elif index < 15:
        return '<amazon:emotion name="disappointed" intensity="{}">'.format(medium_or_low)
    else:
        return '<amazon:emotion name="disappointed" intensity="high">'.format(high_or_medium)
        
        
def get_excitement_suffix(handler_input):
    if is_spanish(handler_input):   # emotions only supported for English voices 
        return ""
    return '</amazon:emotion>'


def normalize_score(score):
    if score.find(" to ") != -1:
        res = score.split(" ")
        if res[2] > res[0]:
            score = res[2] + " " + res[1] + " " + res[0]
        score = score.replace("0", "nil")
        return score
    else:
        return score

    
def get_one_line(noun1, article1, noun2, article2, noun3, article3):
    found_number_or_none = re.search("[0-9]", noun1)
    found_number = False if found_number_or_none is None else True
    
    found_nil = noun1.find('nil')
    
    noun3 = normalize_score(noun3)
    if found_number or found_nil != -1:
        return noun1 + "<break time='350ms'/>" + noun2
    else:
        return noun1 + article1 + noun2 + article2 + noun3 + article3 + ","


def load_stats(number, filename, article1, article2, article3, firstCol, secondCol, thirdCol):
    say = ""
    card_text = ""
    s3 = boto3.client("s3")
    bucket = "bpltables"
    logger.info('try to open file ' + bucket + ":" + filename)
    resp = s3.get_object(Bucket=bucket, Key=filename)
    body_str = resp['Body'].read().decode("utf-8")
    logger.info("converted streaming_body to string")
    logger.info(body_str)
    n = body_str.split("\n")
    oneCard = n[0].split(',')
    
    for index in range(0,number):
        oneCard = n[index].split(',')
        third = oneCard[thirdCol] if thirdCol > -1 else ""
        new_text = get_one_line(oneCard[firstCol], article1, oneCard[secondCol], article2, third, article3)
        say = say + ", " + new_text
        card_text = card_text + new_text + "\n"
        #logger.info("building at index {} {}".format(index, say))
    return (say, strip_emotions(card_text))


def load_combined_stats(number, filename, firstCol, secondCol, thirdCol):
    s3 = boto3.client("s3")
    bucket = "bpltables"
    logger.info('try to open file ' + bucket + ":" + filename)
    resp = s3.get_object(Bucket=bucket, Key=filename)
    body_str = resp['Body'].read().decode("utf-8")
    n = body_str.split("\n")
    oneCard = n[0].split(',')
    names = []
    goals = []
    saves = []

    for index in range(0,number):
        oneCard = n[index].split(',')
        names.append(oneCard[firstCol])
        team_index = find_team_index(oneCard[secondCol])
        saves.append(int(oneCard[thirdCol]))
        goals.append(table_data[team_index][GOALS_AGAINST_INDEX])
    return (names,goals,saves)


def load_two_stats(number, filename):
    s3 = boto3.client("s3")
    bucket = "bpltables"
    logger.info('load_two_stats try to open file ' + bucket + ":" + filename)
    try:
        resp = s3.get_object(Bucket=bucket, Key=filename)
        body_str = resp['Body'].read().decode("utf-8")
        n = body_str.split("\n")
        oneCard = n[0].split(',')
        names = []
        stat1 = []
        stat2 = []
        logger.info(f"opened file {n} {oneCard}")
        for index in range(0,number):
            oneCard = n[index].split(',')
            names.append(oneCard[0])
            stat1.append(int(oneCard[1]))
            stat2.append(int(oneCard[2]))
        logger.info("retrieved data")
        return (names,stat1,stat2)
    except Exception as ex:
         logger.error(ex)

    
def load_stats_ng(handler_input, number, filename, article1, article2, article3, firstCol, secondCol, thirdCol, team_to_match, lines_to_skip=0):
    _ = set_translation(handler_input)
    say = ""
    card_text = ""
    s3 = boto3.client("s3")
    bucket = "bpltables"
    logger.info('try to open file ' + bucket + ":" + filename)
    resp = s3.get_object(Bucket=bucket, Key=filename)
    body_str = string_data = resp['Body'].read().decode("utf-8")
    logger.info("converted streaming_body to string")
    logger.info("load_stats_ng, lines_to_skip:" + str(lines_to_skip))
    #logger.info(body_str)
    n = body_str.split("\n")
    lines_in_file = len(n)
    logger.info(f"there are {len(n)} items in the list")
    oneCard = n[0].split(',')
    date_lines = 0;
    index = 0
    skip_index = 0
    while skip_index < (lines_to_skip):
        if index >= lines_in_file:
            break
        oneCard = n[index].split(',')
        if oneCard[0] == 'date':
            index += 1
            date_lines += 1;
            logger.info("increment index but don't increment lines to skip")
        else:
            index += 1
            skip_index += 1
            logger.info("we have seen one of the lines to skip")

    logger.info(f"index: {index} number:{number} date_lines: {date_lines} lines_to_skip: {lines_to_skip}")
    last_line_was_a_date = False
    
    try:
        while (index < (number + date_lines + lines_to_skip)) and (index < lines_in_file):
            oneCard = n[index].split(',')
            if oneCard[0] == 'date':
                if last_line_was_a_date == False:
                    say += ' ' + oneCard[1] + ' '
                    last_line_was_a_date = True
                date_lines += 1;
            else:
                third = oneCard[thirdCol] if thirdCol > -1 else ""
                try:
                    if ":" in third:
                        x = third.split(":")
                        third =  get_tz_adjusted_time(handler_input, x[0], x[1])
                except Exception as ex:
                    logger.info("exception getting tz")
                    logger.info(ex)
                new_text = ""
                try:
                    new_text = get_one_line(oneCard[firstCol], article1, oneCard[secondCol], article2, third, article3)
                except Exception as ex:
                    logger.info(ex)
                    logger.info(f"error calling get_one_line, {index}")
                    break
                if team_matches(team_to_match, new_text):
                    say = say + ", " + new_text
                    card_text = card_text + new_text + "\n"
                    last_line_was_a_date = False
                else:
                    date_lines += 1
            index += 1
    except:
        logging.info("RAN OFF END OF LIST OF FIXTURES OR RESULTS")
        #say += _(" that is the end of the list. ")
    if is_spanish(handler_input):
        if has_screen(handler_input):
            say = say.replace("oh clock", "00")
        else:
            say = say.replace("oh clock", "")
    return (say, strip_emotions(card_text))            


''' adjust the input time to the already determined timezone '''
def get_tz_adjusted_time(handler_input, local_hour, local_minute):
    session_attr = handler_input.attributes_manager.session_attributes
    last_local_time   = session_attr.get("local_time", None)
    last_local_hour   = session_attr.get("local_hour", None)
    last_local_minute = session_attr.get("local_minute", None)
    if (local_hour == last_local_hour) and (last_local_minute == local_minute) and (last_local_time is not None):
        return last_local_time

    userTimeZone = session_attr.get("timezone", None)
    #userTimeZone = get_time_zone(handler_input)
    lambda_client = boto3.client("lambda")
    body = '{"hour":"' + str(local_hour) + '","minute":"' +  str(local_minute) +  '","dest_timezone":"' +  userTimeZone +  '"}'
    logger.info("body is " + body)
    resp = lambda_client.invoke(FunctionName="timezone", Payload=body)
    payload = resp['Payload'].read().decode("utf-8")
    jpay = json.loads(payload)
    local_time = jpay.get("body")    
    session_attr["local_hour"] = local_hour
    session_attr["local_minute"] = local_minute
    session_attr["local_time"] = local_time
    handler_input.attributes_manager.session_attributes = session_attr
    logger.info("local time is " + str(local_time))
    return local_time



''' Accept a cannonical name from Speech Model such as "tottenhamhotspurs" , convert to name as in text files and look for a match'''
def team_matches(team_name, text_to_search):
    #logger.info(f"team_matches {team_name} {text_to_search}")
    if team_name == "":
        return True
    cannonical_names = {
        #"as appears in table" : "as appears in results"
        "Arsenal"           : "Arsenal",
        "Aston Villa"       : "Aston Villa",
        "Burnley"           : "Burnley",
        "Brentford"         : "Brentford",
        "Brighton and Hove Albion" : "Brighton",
        "Chelsea"           : "Chelsea",
        "Crystal Palace"    : "Crystal Palace",
        "Everton"           : "Everton",
        "Leeds United"      : "Leeds",
        "Leicester City"    : "Leicester",
        "Liverpool"         : "Liverpool",
        "Manchester United" : "Manchester United",
        "Manchester City"   : "Manchester City",
        "Newcastle United"  : "Newcastle",
        "Norwich City"      : "Norwich",
        "Southampton"       : "Southampton",
        "Tottenham Hotspur" : "Tottenham Hotspur", 
        "Watford"           : "Watford",
        "Westham United"    : "West Ham",
        "Wolverhampton Wanderers" : "Wolves"
    }
    name_to_look_for = cannonical_names.get(team_name, "not found")
    match_index = text_to_search.upper().find(name_to_look_for.upper())
    if match_index == -1:
        pass
        #logger.info(f"{name_to_look_for} not found in {text_to_search}")
    else:
        logger.info(f"{name_to_look_for} FOUND in {text_to_search}")
    return match_index != -1
    

def find_team_index(team_id):
    reload_main_table_as_needed()
    for index, team in enumerate(table_data):
        if team[NAME_INDEX].upper().replace(" ", "") == team_id.upper().replace(" ", ""):
            return index
        if team[NAME_INDEX].upper().replace(" ", "") == team_id.upper():
            return index
    logger.info(f"did not find {team_id} in {str(table_data)}")
    return -1

    
def team_results_or_fixtures(handler_input, team_name, results_or_fixtures):
    _ = set_translation(handler_input)
    intro = _("recent results for {} were").format(team_name) if results_or_fixtures == "prevWeekFixtures" else _("upcoming fixtures for {} are").format(team_name)

    speech, card_text = load_stats_ng(handler_input, 5, results_or_fixtures, "  ", "  ", "  ", 0, 2, 1, team_name)
    speech = intro + speech + ',' + _("press a button")
    card = SimpleCard("Results", card_text)
    if is_spanish(handler_input):
        str1 = speech.replace("beat", "vencer").replace("lost to", "perdió ante").replace("drew", "Empate").replace(" to ", " por ")
        str1 = day_of_week_trans(handler_input,str1)
        str1 = month_trans(handler_input, str1)
        speech = str1

    if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
        card = None
    handler_input.response_builder.ask(speech).set_card(card).add_directive(
          APLARenderDocumentDirective(
            token= "tok",
            document = {"type" : "Link", "src"  : doc},
            datasources = {"user": {"name": wrap_language(handler_input, speech)},"crowd": {"noise": noise3,"start": str(randrange(0, noise3_max_millis))}
            }
            )
        )
    return handler_input.response_builder.response    
    
''' set the timezone based on handler_input '''
def set_time_zone(handler_input):
    session_attr = handler_input.attributes_manager.session_attributes
    tz = session_attr.get("timezone", None)
    if tz is not None:
        return
    sys_object = handler_input.request_envelope.context.system
    device_id = sys_object.device.device_id

    # get Alexa Settings API information
    api_endpoint = sys_object.api_endpoint
    api_access_token = sys_object.api_access_token
    #logger.info(f"sys_object {sys_object} token {api_access_token}")

    # construct systems api timezone url
    url = '{api_endpoint}/v2/devices/{device_id}/settings/System.timeZone'.format(api_endpoint=api_endpoint, device_id=device_id)
    headers = {'Authorization': 'Bearer ' + api_access_token}

    userTimeZone = ""
    try:
        r = requests.get(url, headers=headers)
        res = r.json()
        logger.info("Device API result: {}".format(str(res)))
        userTimeZone = res
        logger.info("********** got TZ ***************")
        # lambda_client = boto3.client("lambda")
        # body = '{"hour":"7","minute":"30","dest_timezone":"' + userTimeZone + '"}'
        # #logger.info("body is " + body)
        # resp = lambda_client.invoke(FunctionName="timezone", Payload=body)
        # payload = resp['Payload'].read().decode("utf-8")
        # jpay = json.loads(payload)
        # #logger.info(f'the time in {userTimeZone} is {jpay.get("body")}')
        
        session_attr["timezone"] = userTimeZone
        handler_input.attributes_manager.session_attributes = session_attr
        #return jpay.get("body")
    except Exception as ex:
        logger.info("could not get timezone " + str(ex))
        #return None
    
