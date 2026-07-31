pipeline {
    agent { label 'python' }
    environment {
        // site specifics
        AUTHOR = "Ramon Garcia"
        ACCOUNT = "monfg"
        DOMAIN = "codeberg.org"
        SITE_NAME = "${ACCOUNT}.${DOMAIN}"
        SITE_TITLE = "${AUTHOR}'s blog"

        // build specifics
        SOURCE = "blog"
        SITE_DIR = "site"
        GIT_URL = "ssh://git@192.168.0.110:/home/git/projects/${SOURCE}.git"

        // Codeberg pages specifics
        SITE_PAGES = "page"
        SITE_PAGES_URL = "ssh://git@codeberg.org/${ACCOUNT}/${SITE_PAGES}.git"
        BASE_URL = "https://${ACCOUNT}.${DOMAIN}/${SITE_PAGES}/${SITE_DIR}"

        // neocities base url:  BASE_URL = "https://${ACCOUNT}.${DOMAIN}/${SITE_PAGES}

        TRACKING_URL = "https://${ACCOUNT}.goatcounter.com"
        LOCAL_BASE_URL = "http://127.0.0.1:2080"
        DEST = "./${SITE_DIR}"
        SRC = "./${SOURCE}"
        LOCAL_PATH_ROOT = "/opt/deploy"
        LOCAL_PATH = "${LOCAL_PATH_ROOT}/site"
        STABLE = "./last"

        // blog path specifics
        STATICS_IMG = ".ico,.webp"
        STATICS_ASSETS = ".css"

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
                        dir("${SITE_PAGES}") { deleteDir() }
                        dir("${SITE_DIR}") { deleteDir() }
                        sh '''
                            git clone ${GIT_URL}
                        '''
                    } else {
                        if (fileExists("/home/jenkins/agent/workspace/${SOURCE}")) {
                            sh '''
                            echo "Source is already present"
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
                    mkdir -p ${DEST}
                    $HOME/.local/bin/uv run build_blog.py
                    '''
                }
            }

        }
        stage('Local Publish') {
            steps {
                sh """
                mkdir -p ${LOCAL_PATH}
                mkdir -p ${STABLE}/${SITE_DIR}
                cp -r ${LOCAL_PATH} ${STABLE}/
                cp -r ${DEST} ${LOCAL_PATH_ROOT}
                find ${LOCAL_PATH} -type f -exec sed -i 's|${BASE_URL}|${LOCAL_BASE_URL}/${SITE_DIR}|g' {} +
                if [ ! -z "${TRACKING_URL}" ]; then
                  find ${LOCAL_PATH} -type f -exec sed -i 's|.*${TRACKING_URL}.*|<!-- no tracking -->|g' {} +
                fi
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

        stage('Go Live in Codeberg') {
            steps {
                catchError (buildResult: 'NOT_BUILT', stageResult: 'FAILURE', message: 'Failed to update fallback page'){
                    sh '''
                        pwd
                        cd ..
                        git clone ${SITE_PAGES_URL}
                        cp -r ${SOURCE}/${SITE_DIR} ${SITE_PAGES}
                        cd  ${SITE_PAGES}
                        git add -A
                        git commit -am "$(date +'%Y-%m-%d %H:%M:%S')"
                        git push origin master
                        cd ..
                    '''
                }
            }
        }
        stage('Go Live in Neocities') {
            steps {
                catchError (buildResult: 'NOT_BUILT', stageResult: 'FAILURE', message: 'Failed to update page'){
                    sh '''
                        cd ..
                        cd ${SOURCE}
                        $HOME/.local/bin/uv run neocities_upload.py
                        cd ..
                    '''
                }
            }
        }
    }
    post {
        aborted {
            sh """
            echo 'Rolling back local changes'
            cp -r ${STABLE}/${SITE_DIR} ${LOCAL_PATH_ROOT}
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
                    dir("${SITE_PAGES}") { deleteDir() }
                }
            }
        }
    }
}
