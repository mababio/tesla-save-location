FROM python:3.10-slim

######create appuser and directory for app#########
RUN groupadd -g 999 appuser && \
    useradd -m -r -u 999 -g appuser appuser
USER appuser
ENV APP_HOME  /home/appuser/app
RUN mkdir /home/appuser/app
RUN chown appuser:appuser /home/appuser/app
###### Create appuser and directory for application#########

WORKDIR $APP_HOME
COPY src/* ./

###### Create Python Virutal evironment ###########
RUN python -m venv $APP_HOME
RUN . $APP_HOME/bin/activate && pip install -r requirements.txt
# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1
###### Create Python Virutal evironment ###########

####### Application specfic varaibles ##########

#################### For folks who are not creating kubernetes secrets ####################
#            ENV MYQ_USERNAME <VALUE>
#            ENV MYQ_PASSWORD <VALUE>
#            ENV CHANIFY_KEY <VALUE>
#            ENV TESLA_CONTROL_SERVICES_BASE_URL <VALUE>
#            ENV TESLA_DATA_SERVICES_BASE_URL <VALUE>
#################### For folks who are not creating kubernetes secrets ####################
####### Application specfic varaibles ##########

ENTRYPOINT . $APP_HOME/bin/activate && python main.py