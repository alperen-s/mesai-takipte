KeyError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/mesai-takipte/app.py", line 52, in <module>
    st.page_link("app.py", label="Ana Sayfa", icon="🏠")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 628, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 1354, in page_link
    return self._page_link(
           ~~~~~~~~~~~~~~~^
        page=page,
        ^^^^^^^^^^
    ...<6 lines>...
        query_params=query_params,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/button.py", line 1666, in _page_link
    url_pathname = page_data["url_pathname"]
                   ~~~~~~~~~^^^^^^^^^^^^^^^^
