# Go-to-the-source! (towards accountable LLMs)

Let's make LLMs accountable! They are trapped in a cage without Internet connection, but we can provide them with what they need to support their claims. Given a claim, we are going to make them search Google until they find a source that supports it! Because we are whole-hearted, we are then also going to give them the chance to either confirm or dismiss what they said, and instead provide a different answer.

To try this prototype, you will need programmatic access to the Google Search API and the Open AI API. Then, set the following environment variables: `GOOGLE_API_KEY`, `GOOGLE_API_CX`, `OPENAI_KEY`.

You will also need a couple of dependencies installed in your environment (see [requirements.txt](requirements.txt)), as well as Chromium + a compatible chromium driver for Selenium in PATH.

Then: `python3 -m go_to_the_source`

## Example:

```
Please input a simple (single-line) prompt that you want to make to GPT-3: When did Antonio Banderas win an oscar?
GPT-3 says: 

Antonio Banderas has not won an Oscar. He has been nominated for one, for his performance in the 1999 film "The Mask of Zorro".
.
.
.
Got it, must visit https://en.wikipedia.org/wiki/List_of_awards_and_nominations_received_by_Antonio_Banderas to confirm your claim!
.
.
.
After reading this content, would you say the answer "When did Antonio Banderas win an oscar?" to the question "Antonio Banderas has not won an Oscar." has been confirmed or contradicted?
Please answer one of the three options: "Yes, confirmed", "Neither confirmed nor contradicted" or "Contradicted, I now think the right answer is: ..."

GPT-3 answers:
Yes, confirmed
```

## How it works

![Sequence diagram](diagram.png)