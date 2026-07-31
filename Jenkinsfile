pipeline {
    agent { label 'python' }
    environment {
        // site specifics
        AUTHOR = "Ramon Garcia"
        ACCOUNT = "ramongarciamx"
        EMAIL = "${ACCOUNT}@proton.me"
        TITLE = "Ramon's blog"
        SITE_NAME = "ramongarciamx"
        SOURCE = "rgarciamx"

        //build specifics
        GIT_URL = "ssh://git@192.168.0.110:/home/git/projects/${SOURCE}.git"
        TRACKING = "https://${ACCOUNT}.goatcounter.com"
        BASE_URL = "https://${ACCOUNT}.neocities.org"
        LOCAL_BASE_URL = "http://127.0.0.1:2080"
        DEST = "./site"
        SRC = "./${SOURCE}"
        YEAR_LOOKBACK = 1

        //blog path specifics
        STATICS_IMG = ".ico,.webp"

    }
    parameters {
        booleanParam(
            name: 'FORCE_SETUP',
            defaultValue: false,
            description: 'Force a fresh installation of uv and sync environment'
        )
        booleanParam(
            name: 'CLEAN_REPOSITORIES',
            defaultValue: false,
            description: 'Remove the repositories in the workspace'
        )
        booleanParam(
            name: 'LOCAL_VALIDATION',
            defaultValue: true,
            description: 'Execute a local deployment to validate results'
        )
        booleanParam(
            name: 'UPDATE_RSS',
            defaultValue: true,
            description: 'Update the RSS feed (only works for Posts)'
        )
    }
    stages {
        stage('Environment Setup') {
            steps {
                script {
                    if (!fileExists('/home/jenkins/.local/bin/uv') || params.FORCE_SETUP) {
                        sh '''
                            curl -LsSf https://astral.sh/uv/install.sh | sh
                            export PATH="$HOME/.local/bin:$PATH"
                            uv sync --frozen
                        '''
                    }
                }
            }
        }
        stage('Sources Setup') {
            steps {
                script {
                    if (params.CLEAN_REPOSITORIES) {
                        dir("${SOURCE}") { deleteDir() }
                        dir("site") { deleteDir() }
                        sh '''
                            git clone ${GIT_URL}
                        '''
                    } else {
                        if (fileExists("/home/jenkins/agent/workspace/blog/${SOURCE}")) {
                            sh '''
                            cd ${SOURCE}
                            git pull
                            cd ..
                            '''
                        } else {
                            sh '''
                            git clone ${GIT_URL}
                            '''
                        }
                    }
                }
            }

        }
        stage('Run Tests') {
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
              sh '''
              $HOME/.local/bin/uv run pytest
              '''
            }
          }
        }
        stage('Build') {
            steps {
                script {
                    if (params.UPDATE_RSS) {
                      environment {
                        UPDATE_RSS = true
                      }
                    }
                    sh '''
                    mkdir -p ./site
                    $HOME/.local/bin/uv run build_blog.py
                    '''
                }
            }

        }
        stage('Local Publish') {
            steps {
                sh """
                mkdir -p /opt/deploy/site
                mkdir -p ./last/site
                cp -r /opt/deploy/site ./last/
                cp -r ./site /opt/deploy/
                find /opt/deploy/site -type f -exec sed -i 's|${BASE_URL}|${LOCAL_BASE_URL}/site|g' {} +
                find /opt/deploy/site -type f -exec sed -i 's|.*${TRACKING}.*|    <!-- no tracking -->|g' {} +
                """
            }
        }
        stage('Promote Release') {

            when {
                expression {
                    params.LOCAL_VALIDATION == true
                }
            }
            options {
                timeout time: 3, unit: 'MINUTES'
            }
            steps {
                script {
                    try {
                        input message: 'Promote the latest update?', ok: 'Publish', cancel: 'Reject'
                    } catch (err) {
                        currentBuild.result = 'ABORTED'
                        error('Publish was rejected')
                    }
                }
            }
        }

        stage('Go Live') {
            steps {
                catchError (buildResult: 'NOT_BUILT', stageResult: 'FAILURE', message: 'Failed to update fallback page'){
                    sh '''
                        $HOME/.local/bin/uv run neocities_upload.py
                    '''
                }
            }
        }
    }
    post {
        aborted {
            sh """
            echo 'Rolling back local changes'
            cp -r ./last/site /opt/deploy/
            """
        }
        failure {
            echo 'Upon failure you should clean repositories for the next run!'
            cleanWs()
        }
        cleanup {
            script {
                if (params.CLEAN_REPOSITORIES) {
                    dir("${SOURCE}") { deleteDir() }
                    dir("site") { deleteDir() }
                }
            }
        }
    }
}
