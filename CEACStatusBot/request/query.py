import requests
from bs4 import BeautifulSoup
import time

from CEACStatusBot.captcha import CaptchaHandle, OnnxCaptchaHandle


def query_status(application_num, passport_number, surname, captchaHandle: CaptchaHandle = OnnxCaptchaHandle("captcha.onnx")):
    failCount = 0
    result = {"success": False}

    while failCount < 5:
        if failCount > 0:
            time.sleep(5)
        failCount += 1

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        session = requests.Session()
        ROOT = "https://ceac.state.gov"

        try:
            r = session.get(f"{ROOT}/ceacstattracker/status.aspx?App=IV", headers=headers)
        except Exception as e:
            print("GET failed:", e)
            continue

        soup = BeautifulSoup(r.text, "lxml")

        captcha_img = soup.find("img", id="c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage")
        if not captcha_img:
            print("Captcha image not found on initial page.")
            continue

        img_url = ROOT + captcha_img["src"]
        img_resp = session.get(img_url)
        captcha_value = captchaHandle.solve(img_resp.content)

        def copy_hidden(name, data):
            el = soup.find("input", {"name": name})
            if el:
                data[name] = el.get("value", "")

        data = {
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnSubmit",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "ctl00$ContentPlaceHolder1$Visa_Case_Number": application_num,
            "ctl00$ContentPlaceHolder1$Passport_Number": passport_number,
            "ctl00$ContentPlaceHolder1$Surname": surname,
            "ctl00$ContentPlaceHolder1$Captcha": captcha_value,
        }

        for field in [
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
            "LBD_VCID_c_status_ctl00_contentplaceholder1_defaultcaptcha",
            "LBD_BackWorkaround_c_status_ctl00_contentplaceholder1_defaultcaptcha",
        ]:
            copy_hidden(field, data)

        try:
            r = session.post(f"{ROOT}/ceacstattracker/status.aspx", headers=headers, data=data)
        except Exception as e:
            print("POST failed:", e)
            continue

        # Wait 5 seconds after submission
        time.sleep(5)

        soup = BeautifulSoup(r.text, "lxml")

        # DEBUG: print first 1000 chars of response to see what page returned
        print("POST response preview:\n", r.text[:1000])

        # Search for status and case elements
        status_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblStatus")
        case_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblCaseNo")
        print("status_el:", status_el)
        print("case_el:", case_el)

        if not status_el or not case_el:
            print("Status or Case element not found, retrying...")
            continue

        msg_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblMessage")
        visa_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblAppName")

        result.update({
            "success": True,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "visa_type": visa_el.text.strip() if visa_el else "IV",
            "status": status_el.text.strip(),
            "description": msg_el.text.strip() if msg_el else "",
            "application_num": case_el.text.strip(),
            "application_num_origin": application_num,
            "case_created": None,
            "case_last_updated": None,
        })

        break

    return result
