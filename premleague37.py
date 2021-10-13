# -*- coding: utf-8 -*-
"""
Python 3.7 version of PremierLeague.
TODO: 
full regression test
split source code into multiple files
add team sounds
copy india voice model to other models
"""
#from utility import foo, GoalsHandler
import shared
import random
import logging
import pprint
import json
import boto3
from random import randrange
import random
import re
import requests
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name, get_intent_name, get_slot, get_slot_value, get_supported_interfaces
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard, StandardCard, Image
from ask_sdk_model import Response
#from ask_sdk_model.interfaces.alexa.presentation.apla import RenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective as APLRenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apla import RenderDocumentDirective as APLARenderDocumentDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import (SetValueCommand, ExecuteCommandsDirective)
from ask_sdk_core.utils.viewport import get_viewport_profile

#from statshandlers import bla
from shared import extra_cmd_prompts, doc, noise, noise2, noise3, noise_max_millis, noise2_max_millis, noise3_max_millis, datasources2, datasourcessp, test_speach_data, noise_data, teamsdatasource
from statshandlers import load_suggestions, suggest, strip_emotions, get_excitement_prefix, reload_main_table_as_needed, team_handler 
from statshandlers import get_excitement_suffix,normalize_score, get_one_line, GoalsHandler, random_phrase, build_table_fragment
from statshandlers import random_prompt, pluralize, load_stats, ListTeamNamesHandler, CleanSheetsHandler,FoulsHandler, RelegationHandler
from statshandlers import RedCardHandler, YellowCardHandler, TouchesHandler, TacklesHandler, RefereesHandler
from statshandlers import ResultsHandler, FixturesHandler,TableHandler, load_stats_ng, set_time_zone,load_combined_stats
from multimedia import ButtonEventHandler, AddTeamIntentHandler, RemoveTeamIntentHandler, go_home, get_line_chart_url, do_line_graph
from datetime import datetime
import gettext
from statshandlers import wrap_language, set_translation, is_spanish
lang_translations_en = gettext.translation('base', localedir='locales', languages=['en'])
lang_translations_en.install()
lang_translations_sp = gettext.translation('base', localedir='locales', languages=['es'])
lang_translations_sp.install()
#_ = gettext.translation('base', localedir='locales', languages=['en']).gettext
#tr = lang_translations_en.gettext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SKILL_NAME = "PremierLeague"
HELP_REPROMPT = 'What can we help you with?'

sb = SkillBuilder()
sns_client = boto3.client('sns')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# table_data = []
# table_index = 0
TOKEN = "buttontoken"
TICK_WIDTH = 3.0

# def set_translation(handler_input):
#     #global tr
#     #global _
#     logger.info("at set_translation {}".format(handler_input.request_envelope.request.locale))
#     if handler_input.request_envelope.request.locale == "en-US":
#         _  = lang_translations_en.gettext
#         #tr = lang_translations_en.gettext
#         logger.info("ENGLISH")
#     else:
#         _  = lang_translations_sp.gettext
#         #tr = lang_translations_sp.gettext
#         logger.info("SPANISH")
#     return _
#     #logger.info("returning _ after set_translation English:{} Spanish:{} underbar:{} tr:{}".format(lang_translations_en, lang_translations_sp, _, tr))
    
class WelcomeHandler(AbstractRequestHandler):
    """Handler for StartIntent."""

    def can_handle(self, handler_input):
        return (is_request_type("LaunchRequest")(handler_input))

    def handle(self, handler_input):
        try:
            _ =set_translation(handler_input)
            language_now = "SPANISH" if _ == lang_translations_sp.gettext else "ENGLISH"
            logger.info(language_now)
            #tr = lang_translations_en.gettext
            #_ = lang_translations_en.gettext
            logger.info("english: {}".format(lang_translations_en.gettext('Welcome to PremierLeague')))
            logger.info("spanish: {}".format(lang_translations_sp.gettext('Welcome to PremierLeague')))
            logger.info("underbr: {}".format(_('Welcome to PremierLeague')))
            #logger.info("tr:      {}".format(tr('Welcome to PremierLeague')))

            WELCOME_MESSAGE = _('Welcome to PremierLeague')
            logger.info("In WelcomeHandler {}".format(WELCOME_MESSAGE))
        except Exception as ex:
            logging.exception("error at start")
        # if is_spanish(handler_input):
        #     datasources2["gridListData"]["title"] = "Puedes preguntar sobre"
        #     datasources2["gridListData"]["listItems"][0]["primaryText"] = "La mesa"
        #     datasources2["gridListData"]["listItems"][1]["primaryText"] = "los fósforos"
        #     datasources2["gridListData"]["listItems"][2]["primaryText"] = "Resultados"
        #     datasources2["gridListData"]["listItems"][3]["primaryText"] = "Equipos"
        #     datasources2["gridListData"]["listItems"][4]["primaryText"] = "Puntos por semana"
        #     datasources2["gridListData"]["listItems"][5]["primaryText"] = "Descenso"
        #     datasources2["gridListData"]["listItems"][6]["primaryText"] = "Sábanas limpias"
        #     datasources2["gridListData"]["listItems"][7]["primaryText"] = "Faltas"
        #     datasources2["gridListData"]["listItems"][8]["primaryText"] = "Metas"
        #     datasources2["gridListData"]["listItems"][9]["primaryText"] = "Diferencia de goles"

        
        load_suggestions(handler_input)
        speech, card_text = load_stats_ng(handler_input, 1, "prevWeekFixtures", "  ", "  ", "  ", 0, 2, 1, "")
        speech2, card_text2 = load_stats_ng(handler_input, 1, "fixtures2", ' versus ', ' at ', "  ", 0, 2, 1, "")
        welcome = WELCOME_MESSAGE + _(',, The last result was {} and the next match is {},, ').format(speech,speech2)
        set_time_zone(handler_input)
        
        if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
            logger.info("this device has a screen")
            response = boto3.client("cloudwatch").put_metric_data(
                Namespace='PremierLeague',
                MetricData=[{'MetricName': 'InvocationsWithScreen','Timestamp': datetime.now(),'Value': 1,},]
            )
            session_attr = handler_input.attributes_manager.session_attributes
            session_attr["radioButtonText"] = "Form"
            session_attr["screen_displayed"] = True
            handler_input.attributes_manager.session_attributes = session_attr
            this_profile = str(get_viewport_profile(handler_input.request_envelope))
            item_heights = {"ViewportProfile.HUB_LANDSCAPE_SMALL": "75%", "ViewportProfile.HUB_LANDSCAPE_MEDIUM": "65%", "ViewportProfile.HUB_LANDSCAPE_LARGE": "55%"}
            this_height = item_heights.get(this_profile, "")
            datasources2["gridListData"]["listItemHeight"] = this_height
            logger.info(f"** Profile {this_profile} height {this_height}")
            
            return (
                handler_input.response_builder
                    .speak(wrap_language(handler_input, welcome + _(" press a button or scroll to see more options")))
                    .set_should_end_session(False)          
                    .add_directive( 
                      APLRenderDocumentDirective(
                        token= TOKEN,
                        document = {
                            "type" : "Link",
                            "token" : TOKEN,
                            "src"  : "doc://alexa/apl/documents/GridList"
                        },
                        datasources = datasourcessp if is_spanish(handler_input) else datasources2 
                      )
                    ).response
                )
        else:        
            logger.info("this device does not have a screen")
            response = boto3.client("cloudwatch").put_metric_data(
                Namespace='PremierLeague',
                MetricData=[{'MetricName': 'InvocationsWithOutScreen','Timestamp': datetime.now(),'Value': 1,},]
            )
            speech = wrap_language(handler_input, welcome + _(' Say get table, or say a team name '))
            handler_input.response_builder.speak(speech).ask(speech).set_card(SimpleCard("Hello PremierLeague", speech))
            return handler_input.response_builder.response



class TeamHandler(AbstractRequestHandler):
    """Handler for TeamIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle TeamHandler")
        #logger.info("intent_name is " + get_intent_name(handler_input))
        return (is_intent_name("TeamIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In TeamHandler")
        return(team_handler(handler_input, None))

        
class AddAllTeamsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        #logger.info("in can_handle AddAllTeamIntentHandler")
        return (is_intent_name("AddAllTeamsIntent")(handler_input))

    def handle(self, handler_input):
        if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
            session_attr = handler_input.attributes_manager.session_attributes
            session_attr["Arsenal"           ] = True
            session_attr["Aston Villa"       ] = True
            session_attr["Burnley"           ] = True
            session_attr["Brentford"         ] = True
            session_attr["Brighton and Hove Albion" ] = True
            session_attr["Chelsea"           ] = True
            session_attr["Crystal Palace"    ] = True
            session_attr["Everton"           ] = True
            session_attr["Leeds United"      ] = True
            session_attr["Leicester City"    ] = True
            session_attr["Liverpool"         ] = True
            session_attr["Manchester United" ] = True
            session_attr["Manchester City"   ] = True
            session_attr["Newcastle United"  ] = True
            session_attr["Norwich City"      ] = True
            session_attr["Southampton"       ] = True
            session_attr["Tottenham Hotspur" ] = True
            session_attr["Watford"           ] = True
            session_attr["West Ham United"    ] = True
            session_attr["Wolverhampton Wanderers" ] = True        
            handler_input.attributes_manager.session_attributes = session_attr
            return(do_line_graph(handler_input))
        else:
            return(handler_input.response_builder.speak("This device does not have a screen, what can we help you with").ask("what can we help you with").response)
        


class StadiumHandler(AbstractRequestHandler):
    """Handler for StadiumIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle StadiumHandler")
        return (is_intent_name("StadiumIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In StadiumHandler")
        if "stadiums" in extra_cmd_prompts:
            del extra_cmd_prompts["stadiums"]
        slot = get_slot(handler_input, "stadiumType")
        dict = slot.resolutions.to_dict()
        success = dict['resolutions_per_authority'][0]["status"]["code"]
        if success == 'ER_SUCCESS_MATCH':
            stadium_id = dict['resolutions_per_authority'][0]["values"][0]["value"]["id"]
            stadium_name = dict['resolutions_per_authority'][0]["values"][0]["value"]["name"]
            logger.info("found stadium {} {}".format(stadium_id, stadium_name))

            s3 = boto3.client("s3")
            bucket = "bpltables"
            key = "stadiums/" + stadium_name
            logger.info('try to open file ' + bucket + ":" + key)
            resp = s3.get_object(Bucket=bucket, Key=key)
            body_str = resp['Body'].read().decode("utf-8")
            logger.info("converted streaming_body to string")
            
            speech = body_str + ',' + random_prompt(handler_input)
        else:
            logger.info("could not find stadium")
            speech = "Sorry, we could not find that stadium"
        #speech = "in development"
        card_text = "in development"
        
        handler_input.response_builder.speak(speech).ask(speech).set_card(SimpleCard("Stadium", card_text))
        return handler_input.response_builder.response


class TeamResultsHandler(AbstractRequestHandler):
    """Handler for TeamResultsIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle TeamResultsHandler")
        return (is_intent_name("TeamResultsIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In TeamResultsHandler")
        if "teamresults" in extra_cmd_prompts:
            del extra_cmd_prompts["teamresults"]
        try:    
            slot = get_slot(handler_input, "plteam")
            dict = slot.resolutions.to_dict()
            success = dict['resolutions_per_authority'][0]["status"]["code"]
            if success == 'ER_SUCCESS_MATCH':
                team_id = dict['resolutions_per_authority'][0]["values"][0]["value"]["id"]
                team_name = dict['resolutions_per_authority'][0]["values"][0]["value"]["name"]
        
            logger.info(f"asked about {team_name}")
            intro = "recent results for {} were".format(team_name)
            session_attr = handler_input.attributes_manager.session_attributes
            handler_input.attributes_manager.session_attributes = session_attr
            
            speech, card_text = load_stats_ng(handler_input, 5, "prevWeekFixtures", "  ", "  ", "  ", 0, 2, 1, team_name)
            speech = intro + speech + ',' + random_prompt(handler_input)
        except Exception as ex:
            logger.info(ex)
            speech = "Sorry we did not understand what team you asked about "
            card_text = speech
        card = SimpleCard("Results", card_text)
        if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
            card = None
        
        handler_input.response_builder.ask(speech).set_card(card).add_directive(
              APLARenderDocumentDirective(
                token= "tok",
                document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": speech},"crowd": {"noise": noise3,"start": str(randrange(0, noise3_max_millis))}
                }
                )
            )
        return handler_input.response_builder.response


class TeamFixturesHandler(AbstractRequestHandler):
    """Handler for TeamFixturesIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle TeamFixturesHandler")
        return (is_intent_name("TeamFixturesIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In TeamFixturesHandler")
        set_time_zone(handler_input)        
        if "teamfixtures" in extra_cmd_prompts:
            del extra_cmd_prompts["teamfixtures"]
        try:    
            slot = get_slot(handler_input, "plteam")
            dict = slot.resolutions.to_dict()
            success = dict['resolutions_per_authority'][0]["status"]["code"]
            if success == 'ER_SUCCESS_MATCH':
                team_id = dict['resolutions_per_authority'][0]["values"][0]["value"]["id"]
                team_name = dict['resolutions_per_authority'][0]["values"][0]["value"]["name"]
            else:
                handler_input.response_builder.speak("Sorry, we did not understand what team you asked about, try again").ask(HELP_REPROMPT)
                return handler_input.response_builder.response
    
            logger.info(f"asked about {team_name}")
            intro = "upcoming fixtures for {} are".format(team_name)
            session_attr = handler_input.attributes_manager.session_attributes
            handler_input.attributes_manager.session_attributes = session_attr
            
            #speech, card_text = load_stats_ng(5, "fixtures2", "  ", "  ", "  ", 0, 2, 1, team_name)
            speech, card_text = load_stats_ng(handler_input, 5, "fixtures2", " versus ", " ", "  ", 0, 2, -1, team_name)
            speech = intro + speech + ',' + random_prompt(handler_input)
        except Exception as ex:
            logger.info(ex)
            speech = "Sorry we did not understand what team you asked about "
            card_text = speech
        card = SimpleCard("Fixtures", card_text)
        if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
            card = None
        
        handler_input.response_builder.ask(speech).set_card(card).add_directive(
              APLARenderDocumentDirective(
                token= "tok",
                document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": speech},"crowd": {"noise": noise,"start": str(randrange(0, noise_max_millis))}
                }
                )
            )
        return handler_input.response_builder.response


class YesHandler(AbstractRequestHandler):
    """Handler for YesIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle YesHandler")
        return (is_intent_name("AMAZON.YesIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In YesHandler")
        _ =set_translation(handler_input)
        more = _('Would you like to hear more?')
        logger.info(f"more: {more}")
        session_attr = handler_input.attributes_manager.session_attributes
        which_list = session_attr.get("which_list", "")
        if which_list == "table":
            current_table_index = session_attr.get('table_index', "")
            logger.info("current_table_index is {}".format(current_table_index))
            card_text = ""
            if current_table_index < 15:
                speech = _('The next five teams in the table are ') + build_table_fragment(current_table_index, handler_input) 
                card_text = strip_emotions(speech)
                speech = speech + _('Would you like to hear more?')
                session_attr["table_index"] = current_table_index + 5
            else:
                speech = _('The last five teams in the table are ') + build_table_fragment(current_table_index, handler_input) 
                card_text = strip_emotions(speech)
                speech = speech + random_prompt(handler_input)
                session_attr["table_index"] = 0
            handler_input.attributes_manager.session_attributes = session_attr
    
            card = SimpleCard("Premier League", card_text)
            if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
                card = None
            handler_input.response_builder.ask(wrap_language(handler_input,speech)).set_card(card).add_directive(
              APLARenderDocumentDirective(token= "tok",document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": speech},"crowd": {"noise": noise,"start": str(randrange(0, noise_max_millis))}
                }
                )
            )
            return handler_input.response_builder.response
        elif which_list == "fixtures":
            intro = _('The next five fixtures are')
            fixture_index = session_attr.get("fixture_index", 0)
            session_attr["fixture_index"] = fixture_index + 5
            handler_input.attributes_manager.session_attributes = session_attr
            speech, card_text = load_stats_ng(handler_input, 5, "fixtures2", " versus ", " ", "  ", 0, 2, 1, "", fixture_index)
            speech = intro + speech + _('Would you like to hear more?')
            card = SimpleCard("Premier League", card_text)
            if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
                card = None
            handler_input.response_builder.ask(speech).set_card(card).add_directive(
              APLARenderDocumentDirective(
                token= "tok",
                document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": wrap_language(handler_input,speech)},"crowd": {"noise": noise,"start": str(randrange(0, noise_max_millis))}
                }
                )
            )
            return handler_input.response_builder.response
        else:
            intro = _('The next five results were')
            results_index = session_attr.get("results_index", 0)
            session_attr["results_index"] = results_index + 5
            handler_input.attributes_manager.session_attributes = session_attr
            speech, card_text = load_stats_ng(handler_input, 5, "prevWeekFixtures", "  ", "  ", "  ", 0, 2, 1, "", results_index)
            speech = intro + speech + _('Would you like to hear more?')
            card = SimpleCard("Premier League", card_text)
            if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
                card = None
            handler_input.response_builder.ask(speech).set_card(card).add_directive(
              APLARenderDocumentDirective(
                token= "tok",
                document = {"type" : "Link", "src"  : doc},
                datasources = {"user": {"name": wrap_language(handler_input,speech)},"crowd": {"noise": noise,"start": str(randrange(0, noise_max_millis))}
                }
                )
            )
            return handler_input.response_builder.response


class NoHandler(AbstractRequestHandler):
    """Handler for NoIntent."""

    def can_handle(self, handler_input):
        #logger.info("in can_handle NoHandler")
        return (is_intent_name("AMAZON.NoIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In NoHandler")
        speech = random_prompt(handler_input);
        handler_input.response_builder.speak(wrap_language(handler_input, speech)).ask(speech)
        return handler_input.response_builder.response

class MainScreenIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        return (is_intent_name("MainScreenIntent")(handler_input))

    def handle(self, handler_input):
        return go_home(handler_input)


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        _ =set_translation(handler_input)
        HELP_MESSAGE = _('Say get table, a team name or nickname, red cards, yellow cards, clean sheets, golden boot, fixtures, results, relegation, referees, stadiums by name, touches, fouls and tackles')
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")

        handler_input.response_builder.speak(HELP_MESSAGE).ask(HELP_REPROMPT).set_card(SimpleCard(SKILL_NAME, HELP_MESSAGE))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        _ =set_translation(handler_input)
        logger.info("In CancelOrStopIntentHandler")
        STOP_MESSAGE = _('Okay, hope to see you next time!')

        handler_input.response_builder.speak(STOP_MESSAGE)
        return(finish(handler_input))


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.

    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        _ =set_translation(handler_input)
        logger.info("In FallbackIntentHandler")
        FALLBACK_MESSAGE = _('Sorry, I did not understand, you can ask for help to get a list of things to ask me')
        FALLBACK_REPROMPT = _('What can I help you with?')

        handler_input.response_builder.speak(FALLBACK_MESSAGE).ask(FALLBACK_REPROMPT)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(handler_input.request_envelope.request.reason))
        #return handler_input.response_builder.response
        return(finish(handler_input))


# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        _ =set_translation(handler_input)
        try:
            if is_intent_name("AMAZON.NavigateHomeIntent"):
                return
            logger.info("In CatchAllExceptionHandler")
            logger.error(exception, exc_info=True)
            logger.info(str(handler_input))
            logger.info(handler_input.request_envelope.request)
        except:
            logger.info("ignore exception during exception handler")

        message = {"CatchAllExceptionHandler": "was called"}                    # UNCOMMENT THIS ONCE WE GO LIVE
        # sns_client.publish(
        #     TargetArn="arn:aws:sns:us-east-1:747458360727:lambdatop",
        #     Message=json.dumps({'default': json.dumps(message)}),
        #     MessageStructure='json')
        apla_runtime_error = _("Sorry, we did not understand, can you try again?")
        handler_input.response_builder.speak(apla_runtime_error).ask(HELP_REPROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(handler_input.request_envelope.request))
        #set_translation(handler_input)


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))


# Register intent handlers
#sb.add_request_handler(GetNewFactHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(WelcomeHandler())
sb.add_request_handler(RelegationHandler())
sb.add_request_handler(TableHandler())
sb.add_request_handler(YesHandler())
sb.add_request_handler(NoHandler())
sb.add_request_handler(TeamHandler())
sb.add_request_handler(ListTeamNamesHandler())
sb.add_request_handler(StadiumHandler())
sb.add_request_handler(RefereesHandler())
sb.add_request_handler(GoalsHandler())
sb.add_request_handler(TouchesHandler())
sb.add_request_handler(FoulsHandler())
sb.add_request_handler(TacklesHandler())
sb.add_request_handler(CleanSheetsHandler())
sb.add_request_handler(RedCardHandler())
sb.add_request_handler(YellowCardHandler())
sb.add_request_handler(FixturesHandler())
sb.add_request_handler(ResultsHandler())
sb.add_request_handler(TeamResultsHandler())
sb.add_request_handler(TeamFixturesHandler())
sb.add_request_handler(ButtonEventHandler())
sb.add_request_handler(AddTeamIntentHandler())
sb.add_request_handler(RemoveTeamIntentHandler())
sb.add_request_handler(MainScreenIntentHandler())
sb.add_request_handler(AddAllTeamsIntentHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# TODO: Uncomment the following lines of code for request, response logs.
sb.add_global_request_interceptor(RequestLogger())
#sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()


######################## Utility functions #######################


def find_team_index(team_id):
    reload_main_table_as_needed()
    for index, team in enumerate(table_data):
        if team[NAME_INDEX].upper().replace(" ", "") == team_id.upper():
            return index
    return -1


def finish(handler_input):
    goodbyes = ["see you later", "thank you", "ok, see you next time", "see you around the league", "Catch ya later",
                "Take it easy","ta ta","take care","cheers","ok, I'm out"]
    if get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
        return (
            handler_input.response_builder
                .speak(goodbyes[randrange(0, 10)])
                .set_should_end_session(True)          
                .add_directive( 
                  APLRenderDocumentDirective(
                    token= "developer-provided-string",
                    document = {
                        "type" : "Link",
                        "token" : "my token",
                        "src"  : "doc://alexa/apl/documents/finish"
                    }
                  )
                ).response
            )
    else:
        the_text = goodbyes[randrange(0, 10)]
        if (randrange(0,100) == 42):
            the_text = "if you're enjoying this, a review would really be appreciated, thank you"
            response = boto3.client("cloudwatch").put_metric_data(
                Namespace='PremierLeague',
                MetricData=[{'MetricName': 'AskForReview','Timestamp': datetime.now(),'Value': 1,},]
            )

        return(handler_input.response_builder.speak(the_text).set_should_end_session(True).response)
