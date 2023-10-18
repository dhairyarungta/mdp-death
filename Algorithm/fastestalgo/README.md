Steps to run week 9 task:

- Using the same virtual env as in week 8 or create new one if you want. Activate the virtual env.

- Change directory to fastest algo, run 

```shell
python __main__.py
```

- Start the inference server:

    - Create a new virtual env or using the same env as above.
    - Activate the virtual env
    - Install the dependencies. Change directory to fastestalgo/inference_server and run 

    ```shell
    pip install -r requirements.txt
    ```
    
    - Start the inference server:

    ```shell
    flask run --port=5000
    ```