# IPK25-CHAT: TCP Chat Server

Author: Martin Vaculik  
School: FIT VUT Brno  
Date: 07-04-2025

## Description

This is a simple TCP chat server built for project assigment purpose [IPK2025PROTOCOL], supporting:

- User authentication via `AUTH`
- Joining chat rooms via `JOIN`
- Display name updates
- Inappropriate message filtering
- Optional message fragmentation for testing segmentation handling

> Note: Regex patterns and segmented message broadcasting were assisted by ChatGPT. The basic socket setup, `bind`, and `broadcast` ideas were also supported by ChatGPT suggestions. All these prompts were based on the ABNF grammar and the TCP protocol specification . [ChatGPT] [RFC5234] [RFC793]

It is expected for users that they will be playing with the code, editing it to ensure that they are testing what they want.

## CLI

```bash
python3 main.py
```

> Note: My testing was done on python3.12 and Ubuntu 22.04.5 LT

## Configuration

You can change the host or port in the runServer() function at the bottom of the script:

```
runServer(host='127.0.0.1', port=4596)
```

## IMPORTANT NOTES

- Hardcoded secret to **password**
- Only support two rooms **default** and **nondefault**
- In case of failing join the user **IS NOT** connected to the last room. He will fail to deliver any messages, which deviates from the original assigment.
- With messages that are equal to `recverr` and `test123` the server simulates sending the **ERROR** packet. User needs to be joined into room to test that.
- `I am terminating the application with SIGINT, which is not ideal, because the socket might not be closed properly!`

## Bibliography

- [RFC793]: Postel, J., "Transmission Control Protocol", RFC 793, DOI 10.17487/RFC0793, September 1981, Available at: <https://www.rfc-editor.org/info/rfc793>
- [RFC5234] Crocker, D. and Overell, P. Augmented BNF for Syntax Specifications: ABNF [online]. January 2008. [cited 2025-04-19]. DOI: 10.17487/RFC5234. Available at: https://datatracker.ietf.org/doc/html/rfc5234
- [ChatGPT]: OpenAI, "ChatGPT", used for assistance in writing regex patterns, socket setup (`bind`, `broadcast`), and message segmentation logic.
- [IPK2025PROTOCOL]: FIT VUT Brno, Dolejska D., "IPK Project 2: Client for a chat server using the IPK25-CHAT protocol", Available at: <https://git.fit.vutbr.cz/NESFIT/IPK-Projects/src/branch/master/Project_2>
