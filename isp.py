from ask_sdk_model.services.monetization import (
    EntitledState, PurchasableState, InSkillProductsResponse, Error,
    InSkillProduct)
from ask_sdk_model.interfaces.monetization.v1 import PurchaseResult
from ask_sdk_model import Response, IntentRequest
from ask_sdk_model.interfaces.connections import SendRequestDirective
from statshandlers import output_right_directive
from shared import noise3, noise3_max_millis, datasources2
import traceback
import logging
import copy
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
 
''' Adjust the main grid of buttons based on any purchase '''
def ds2_advanced_or_not(handler_input):
    english_but_no_isp = ["en-AU", "en-IN"]
    if handler_input.request_envelope.request.locale in english_but_no_isp:
        no_isp = copy.deepcopy(datasources2)
        no_isp["gridListData"]["listItems"].pop(1)
        return no_isp

    #return datasources2
    try:
        my_products = skill_has_products(handler_input)
        if my_products is not None:
            logger.info("has purchase")
            paid = copy.deepcopy(datasources2)
            #paid["gridListData"]["listItems"].pop(1)
            return paid
        else:
            logger.info("no purchase so go grey")
            unpaid = copy.deepcopy(datasources2)
            unpaid["gridListData"]["listItems"][5]["imageSource"] = unpaid["gridListData"]["listItems"][5]["imageSource"].replace(".jpg", "_grey.jpg")
            # for i in range(7,14):
            #     unpaid["gridListData"]["listItems"][i]["imageSource"] = unpaid["gridListData"]["listItems"][i]["imageSource"].replace(".png", "_grey.png")
            #     logger.info(unpaid["gridListData"]["listItems"][i]["imageSource"])
            return unpaid    
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()
        return datasources2
        


def get_all_entitled_products(in_skill_product_list):
    entitled_product_list = [
        l for l in in_skill_product_list if (
                l.entitled == EntitledState.ENTITLED)]
    return entitled_product_list

    
def get_speakable_list_of_products(entitled_products_list):
    product_names = [item.name for item in entitled_products_list]
    if len(product_names) > 1:
        # If more than one, add and 'and' in the end
        speech = " and ".join(
            [", ".join(product_names[:-1]), product_names[-1]])
    else:
        # If one or none, then return the list content in a string
        speech = ", ".join(product_names)
    return speech

    
def get_resolved_value(request, slot_name):
    try:
        return (request.intent.slots[slot_name].resolutions.
                resolutions_per_authority[0].values[0].value.name)
    except (AttributeError, ValueError, KeyError, IndexError):
        return None


def get_spoken_value(request, slot_name):
    try:
        return request.intent.slots[slot_name].value
    except (AttributeError, ValueError, KeyError, IndexError):
        return None


def is_product(product):
    return bool(product)


def is_entitled(product):
    return (is_product(product) and
            product[0].entitled == EntitledState.ENTITLED)


def in_skill_product_response(handler_input):
    locale = handler_input.request_envelope.request.locale
    ms = handler_input.service_client_factory.get_monetization_service()
    return ms.get_in_skill_products(locale)


def skill_has_products(handler_input):
    try:
        logger.info("ISP: at skill_has_products")
        in_skill_response = in_skill_product_response(handler_input)
        #logger.info("ISP: just after in_skill_product_response")
        #logger.info(str(in_skill_response))
        if isinstance(in_skill_response, InSkillProductsResponse):
            entitled_prods = get_all_entitled_products(in_skill_response.in_skill_products)
            if entitled_prods:
                entitled = get_speakable_list_of_products(entitled_prods)
                #logger.info(f"ISP: you own {entitled}")
                return entitled
            else:
                #logger.info("ISP: you do not own any products")
                return None
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()
        return None

               
def list_purchasable_products(handler_input):
    #logger.info("at list_purchasable_products")
    can_buy = ""
    try:
        in_skill_response = in_skill_product_response(handler_input)
        if in_skill_response:
            purchasable = [l for l in in_skill_response.in_skill_products
                           if l.entitled == EntitledState.NOT_ENTITLED and
                           l.purchasable == PurchasableState.PURCHASABLE]

            if purchasable:
                str = get_speakable_list_of_products(purchasable)
                can_buy = str
                #logger.info(str)
            else:
                logger.info("ISP: there are no products available to purchase")
        return can_buy
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()
        
        
def buy_product(handler_input):
    try:
        logger.info("ISP: at buy_product")
        in_skill_response = in_skill_product_response(handler_input)
        if in_skill_response:
            product = [l for l in in_skill_response.in_skill_products]
            #logger.info("about to send the buy directive")
            return handler_input.response_builder.add_directive(
                    SendRequestDirective(
                        name="Buy",
                        payload={"InSkillProduct": {"productId": product[0].product_id}},
                        token="correlationToken")
                ).response
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()


'''
Called by Alexa system to say the results of a purchase attempt.
The ISP process will re-paint the screen so this function should 
cause a proper redraw to occur
'''
def buy_response(handler_input):
    try:
        logger.info("ISP: at buy_response")
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["screen_displayed"] = False
        handler_input.attributes_manager.session_attributes = session_attr
        try:
            in_skill_response = in_skill_product_response(handler_input)
            product_id = handler_input.request_envelope.request.payload.get("productId")
        except:
            logger.error(ex)        
            traceback.print_exc()
            return output_right_directive(handler_input, "In Skill Purchasing is not supported in your locale, please try another request", None, noise3, noise3_max_millis)                    
            
        speech = "Success"

        if in_skill_response:
            product = [l for l in in_skill_response.in_skill_products if l.product_id == product_id]
            #logger.info("ISP: Product = {}".format(str(product)))
            if handler_input.request_envelope.request.status.code == "200":
                purchase_result = handler_input.request_envelope.request.payload.get("purchaseResult")
                if purchase_result == PurchaseResult.ACCEPTED.value:
                    #logger.info("ISP: successful purchase")
                    speech = "You now have access to charts about Vee Eh Are, Attendance, Corners, Possession, Long vs short goals, and Offsides, scroll down to see the new options"
                elif purchase_result in (PurchaseResult.DECLINED.value,PurchaseResult.ERROR.value,PurchaseResult.NOT_ENTITLED.value):
                    speech = ("Purchase declined for {} What can we tell you about Premier League?".format(product[0].name))
                elif purchase_result == PurchaseResult.ALREADY_PURCHASED.value:
                    #logger.info("ISP: at Already purchased product")
                    speech = " You have already purchased the product, thank you. What can we tell you about Premier League?"
                else:
                    # Invalid purchase result value
                    #logger.info("ISP: Purchase result: {}".format(purchase_result))
                    return FallbackIntentHandler().handle(handler_input)
            else:
                #logger.log("ISP: Connections.Response indicated failure. Error: {}".format(handler_input.request_envelope.request.status.message))
                speech = "There was an error handling your purchase request. Please try again or contact us for help"

        #logger.info("ISP: about to call output_right_directive after purchase")
        return output_right_directive(handler_input, speech, None, noise3, noise3_max_millis)                    
    except Exception as ex:
        logger.info("ERROR _____________")
        logger.error(ex)
        traceback.print_exc()

    
def refund_product(handler_input):
    logger.info("ISP: at refund_response")
    try:
        in_skill_response = in_skill_product_response(handler_input)
        if in_skill_response:
            product_category = get_resolved_value(handler_input.request_envelope.request, "productCategory")

            # No entity resolution match
            if product_category is None:
                product_category = "all_access"
            else:
                product_category += "_pack"
            product = [l for l in in_skill_response.in_skill_products]

            #logger.info("ISP: about to SendRequestDirective for cancel")
            return handler_input.response_builder.add_directive(
                SendRequestDirective(
                    name="Cancel",
                    payload={"InSkillProduct": {"productId": product[0].product_id}
                    },
                    token="correlationToken")
            ).response
    except Exception as ex:
        logger.info("ERROR _____________")
        logger.error(ex)
        traceback.print_exc()

    
def cancel_response(handler_input):
    try:
        logger.info("ISP: In CancelResponseHandler")
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["screen_displayed"] = False
        handler_input.attributes_manager.session_attributes = session_attr
        speech = ""
        
        in_skill_response = in_skill_product_response(handler_input)
        product_id = handler_input.request_envelope.request.payload.get("productId")

        if in_skill_response:
            product = [l for l in in_skill_response.in_skill_products if l.product_id == product_id]
            #logger.info("ISP: Found Product = {}".format(str(product)))
            if handler_input.request_envelope.request.status.code == "200":
                logger.info("ISP: got a 200")
                purchase_result = handler_input.request_envelope.request.payload.get("purchaseResult")
                purchasable = product[0].purchasable
                #logger.info(f"ISP: purchasable {purchasable} purchase_result {purchase_result}")
                if purchase_result == PurchaseResult.ACCEPTED.value:
                    speech = ("You have successfully cancelled your subscription. What can we tell you about Premier League?")
                    #logger.info(f"ISP: successful cancel")
                if purchase_result == PurchaseResult.NOT_ENTITLED.value:
                    speech = "No subscription to cancel. What can we tell you about Premier League?"
                    #logger.info("no subscription to cancel")
                if purchase_result == PurchaseResult.DECLINED.value:
                    speech = "What can we tell you about Premier League?"
                    #logger.info("no subscription to cancel")
            else:
                #logger.log("ISP: Connections.Response indicated failure. Error: {}".format(handler_input.request_envelope.request.status.message))
                speech = "There was an error handling your cancellation request. Please try again or contact us for help" 
        #logger.info(f"ISP: about to call output_right_directive after cancellation {speech}")
        return output_right_directive(handler_input, speech, None, noise3, noise3_max_millis)                    
    except Exception as ex:
        logger.info("ERROR _____________")
        logger.error(ex)
        traceback.print_exc()
                 
                        