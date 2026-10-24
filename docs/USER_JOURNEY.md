# Real-life user journey

## Goal

Ask a question about local documents and understand exactly which documents support the answer.

## Normal journey

1. Start ToF Knowledge and open the browser page.
2. Use the bundled demo documents for the first run.
3. Type a question such as the vacation-policy example.
4. Choose **Answer from my documents**.
5. Read the answer.
6. Read the listed sources and matching passages.
7. If needed, use **Search documents** to inspect relevant passages directly.

**Successful end result:** the answer is useful and you can see what document evidence it came from.

## No-evidence journey

Ask a question whose answer is not present in the demo documents.

The correct result is not a confident invention. ToF should make it clear that the available documents do not provide enough support.

## Typical failure

If search or answering cannot connect to the local environment:

1. read the plain-language message in the result area
2. open **Setup & technical details**
3. choose **Find problems**
4. only open the technical details if deeper troubleshooting is needed

## Stop and return later

Use `python3 run.py down` to stop.

Later use `python3 run.py up` and `python3 run.py ui`. Your local document index remains available.
