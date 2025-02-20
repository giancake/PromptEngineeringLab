import requests
import json
import os
import time

def load_config():
    """
    Load config file looking into multiple locations
    """
    config_locations = [
        "./_config",
        "prompt-eng/_config",
        "../_config"
    ]
    
    # Find CONFIG
    config_path = None
    for location in config_locations:
        if os.path.exists(location):
            config_path = location
            break
    
    if not config_path:
        raise FileNotFoundError("Configuration file not found in any of the expected locations.")
    
    # Load CONFIG
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


def create_payload(model, prompt, target="ollama", **kwargs):
    """
    Create the Request Payload in the format required byt the Model Server
    @NOTE: 
    Need to adjust here to support multiple target formats
    target can be only ('ollama' or 'open-webui')

    @TODO it should be able to self_discover the target Model Server
    [Issue 1](https://github.com/genilab-fau/prompt-eng/issues/1)
    """

    payload = None

    if target == "ollama":
        payload = {
            "model": model,
            "prompt": prompt, 
            "stream": False,
        }
        if kwargs:
            payload["options"] = {key: value for key, value in kwargs.items()}

    elif target == "open-webui":
        '''
        @TODO need to verify the forma for 'parameters' for 'open-webui' is correct.
        [Issue 2](https://github.com/genilab-fau/prompt-eng/issues/2)
        '''
        payload = {
            "model": model,
            "messages": [ {"role" : "user", "content": prompt } ]
        }

        payload.update({key: value for key, value in kwargs.items()})

    
    else:
        print(f'!!ERROR!! Unknown target: {target}')
    
    return payload


def model_req(payload=None):
    """
    Issue request to the Model Server
    """
        
    # CUT-SHORT Condition
    try:
        load_config()
    except:
        return -1, f"!!ERROR!! Problem loading prompt-eng/_config"

    url = os.getenv('URL_GENERATE', None)
    api_key = os.getenv('API_KEY', None)
    delta = response = None

    headers = dict()
    headers["Content-Type"] = "application/json"
    if api_key: headers["Authorization"] = f"Bearer {api_key}"

    # Send out request to Model Provider
    try:
        start_time = time.time()
        response = requests.post(url, data=json.dumps(payload) if payload else None, headers=headers)
        delta = time.time() - start_time
    except:
        return -1, f"!!ERROR!! Request failed! You need to adjust prompt-eng/config with URL({url})"

    # Checking the response and extracting the 'response' field
    if response is None:
        return -1, f"!!ERROR!! There was no response (?)"
    elif response.status_code == 200:

        ## @NOTE: Need to adjust here to support multiple response formats
        result = ""
        delta = round(delta, 3)

        response_json = response.json()
        if 'response' in response_json: ## ollama
            result = response_json['response']
        elif 'choices' in response_json: ## open-webui
            result = response_json['choices'][0]['message']['content']
        else:
            result = response_json 
        
        return delta, result
    elif response.status_code == 401:
        return -1, f"!!ERROR!! Authentication issue. You need to adjust prompt-eng/config with API_KEY ({url})"
    else:
        return -1, f"!!ERROR!! HTTP Response={response.status_code}, {response.text}"
    return

###
### DEBUG
###

if __name__ == "__main__":

    # ##
    # ## ZERO SHOT PROMPTING
    # ##

    # from _pipeline import create_payload, model_req

    # #### (1) Adjust the inbounding  Prompt, simulating inbounding requests from users or other systems
    # # MESSAGE = "What is 984 * log(2)"
    # MESSAGE = """Design a robust IT network infrastructure that supports both LAN and WAN access for voice and data applications. Ensure the solution is:
    #             - High-speed and optimized for low latency  
    #             - Scalable for future expansion  
    #             - Secure against cyber threats  
    #             - Equipped with redundancy and failover mechanisms  

    #             Provide a structured solution, covering:
    #             1. Network Architecture (LAN/WAN design, VLANs, topology)  
    #             2. Hardware Requirements (Routers, switches, firewalls, APs)  
    #             3. Quality of Service (QoS for voice & data)  
    #             4. Security Measures (Firewalls, VPN, encryption)  
    #             5. Performance Optimization Techniques (Load balancing, caching, SD-WAN)  
    #             6. Best Practices for Deployment and Maintenance  
    #             """
    # #### (2) Adjust the Prompt Engineering Technique to be applied, simulating Workflow Templates
    # PROMPT = MESSAGE 

    # #### (3) Configure the Model request, simulating Workflow Orchestration
    # # Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
    # payload = create_payload(#target="ollama",
    #                         target="open-webui",
    #                         # model="gemma", 
    #                         # model="llama2",
    #                         # model = "llama3.2",
    #                         # model="phi4:latest",
    #                         model="tinyllama:latest",
    #                         prompt=PROMPT,
    #                         temperature=1.0, 
    #                         num_ctx=100, 
    #                         num_predict=100)

    # ### YOU DONT NEED TO CONFIGURE ANYTHING ELSE FROM THIS POINT
    # # Send out to the model
    # time, response = model_req(payload=payload)
    # print(response)
    # if time: print(f'Time taken: {time}s')

    #
    # FEW SHOTS PROMPTING
    #

    from _pipeline import create_payload, model_req

    #### (1) Adjust the inbounding  Prompt, simulating inbounding requests from users or other systems
    MESSAGE = "My professor in GenAI SDLC has left us an assignment which consist in building a prompt eng lab in python, using the https://chat.hpc.fau.edu/ or Ollama local install LLM servers. I need to know the requirements for building an IT network that supports LAN and WAN access for voice and data applications, that is very fast and renders a good performance"

    #### (2) Adjust the Prompt Engineering Technique to be applied, simulating Workflow Templates
    # FEW_SHOT = "You are a math teacher. If student asked 1 + 1 you answer 2. If student ask 987 * 2 you answer only 1974. Student asked; provide the result only: "
    FEW_SHOT = "You are a network architect specialist. If a client student asked an consult; respond with aan excellent assesment"
    PROMPT = FEW_SHOT + '\n' + MESSAGE 

    #### (3) Configure the Model request, simulating Workflow Orchestration
    # Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
    payload = create_payload(target="ollama",
                            # target="open-webui",
                            # model="gemma", 
                            # model="llama2",
                            model = "llama3.2",
                            # model="phi4:latest",
                            # model="tinyllama:latest",
                            prompt=PROMPT, 
                            temperature=1.0, 
                            num_ctx=100, 
                            num_predict=100)

    ### YOU DONT NEED TO CONFIGURE ANYTHING ELSE FROM THIS POINT
    # Send out to the model
    time, response = model_req(payload=payload)
    print('First response:' + response)
    if time: print(f'Time taken: {time}s')

    # #### (1) Adjust the inbounding  Prompt, simulating inbounding requests from users or other systems
    MESSAGE = response
    
    #### (2) Adjust the Prompt Engineering Technique to be applied, simulating Workflow Templates
    FEW_SHOT = "You are a network architect specialist. Use the information provided, to enrich this assessment"
    PROMPT = FEW_SHOT + '\n' + MESSAGE 
    
    #### (3) Configure the Model request, simulating Workflow Orchestration
    # Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
    payload = create_payload(target="ollama",
                            # target="open-webui",
                            # model="gemma", 
                            # model="llama2",
                            model = "llama3.2",
                            # model="phi4:latest",
                            # model="tinyllama:latest",
                            prompt=PROMPT,
                            temperature=1.0, 
                            num_ctx=100, 
                            num_predict=100)

    ### YOU DONT NEED TO CONFIGURE ANYTHING ELSE FROM THIS POINT
    # Send out to the model
    time, response = model_req(payload=payload)
    print('Second response' + response)
    if time: print(f'Time taken: {time}s')

    # ##
    # ## PROMPT TEMPLATE PROMPTING
    # ##

    # from _pipeline import create_payload, model_req

    # #### (1) Adjust the inbounding  Prompt, simulating inbounding requests from users or other systems
    # MESSAGE = "984 * log(2)"

    # #### (2) Adjust the Prompt Engineering Technique to be applied, simulating Workflow Templates
    # TEMPLATE_BEFORE="Act like you are a math teacher. Answer to this question from an student:"
    # TEMPLATE_AFTER="Provide the answer only. No explanations!"
    # PROMPT = TEMPLATE_BEFORE + '\n' + MESSAGE + '\n' + TEMPLATE_AFTER

    # #### (3) Configure the Model request, simulating Workflow Orchestration
    # # Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
    # payload = create_payload(target="ollama",
    #                         model="llama3.2:latest", 
    #                         prompt=PROMPT, 
    #                         temperature=1.0, 
    #                         num_ctx=100, 
    #                         num_predict=100)

    # ### YOU DONT NEED TO CONFIGURE ANYTHING ELSE FROM THIS POINT
    # # Send out to the model
    # time, response = model_req(payload=payload)
    # print(response)
    # if time: print(f'Time taken: {time}s')