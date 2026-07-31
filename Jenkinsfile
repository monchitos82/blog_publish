pipeline {
    agent { label 'python' }
    environment {
        // site specifics
        AUTHOR = "Ramon Garcia"
        ACCOUNT = "ramongarciamx"
        SITE_NAME = "${ACCOUNT}"
        SITE_TITLE = "${AUTHOR}'s blog"

        // build specifics
        SOURCE = "blog"
        SITE_DIR = "site"
        GIT_URL = "ssh://git@192.168.0.110:/home/git/projects/${SOURCE}.git"

        // Codeberg pages specifics
        SITE_PAGES = "pages"
        SITE_PAGES_URL = "ssh://git@codeberg.org/${ACCOUNT}/${SITE_PAGES}.git"

        // Base URL definitions
        BASE_URL = "https://${ACCOUNT}.codeberg.page"
        LOCAL_BASE_URL = "http://127.0.0.1:2080/${SITE_DIR}"
        TRACKING_URL = ""

        DEST = "../${SITE_DIR}"
        SRC = "../${SOURCE}"
        LOCAL_PATH_ROOT = "/opt/deploy"
        LOCAL_PATH_SITE = "${LOCAL_PATH_ROOT}/site"
        STABLE = "last"

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
        booleanParam(
            name: 'SPELL_CHECK',
            defaultValue: false,
            description: 'Use neuspell for content spellcheck'
        )
        booleanParam(
            name: 'LLM_REVIEW',
            defaultValue: false,
            description: 'Use LLM for content summarization'
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
                        dir("../${SOURCE}") { deleteDir() }
                        dir("../${SITE_DIR}") { deleteDir() }
                        dir("../${STABLE}") { deleteDir() }
                        sh '''
                            cd ..
                            git clone ${GIT_URL}
                        '''
                    } else {
                        if (fileExists("/home/jenkins/agent/workspace/${SOURCE}")) {
                            sh '''
                            echo "Source is already present"
                            cd ..
                            cd ${SOURCE}
                            git pull
                            cd ../blog_builder
                            '''
                        } else {
                            sh '''
                            cd ..
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
                sh '''
                mkdir -p ${LOCAL_PATH_SITE}
                mkdir -p ../${STABLE}/${SITE_DIR}
                cp -r ${LOCAL_PATH_SITE} ../${STABLE}/
                cp -r ${DEST} ${LOCAL_PATH_ROOT}
                find ${LOCAL_PATH_SITE} -type f -exec sed -i "s|${BASE_URL}|${LOCAL_BASE_URL}|g" {} +
                if [ ! -z "${TRACKING_URL}" ]; then
                  find ${LOCAL_PATH_SITE} -type f -exec sed -i "s|.*${TRACKING_URL}.*|<!-- no tracking -->|g" {} +
                fi
                '''
            }
        }
        stage('Spell Check Content') {
            when {
                expression {
                    params.SPELL_CHECK == true && params.LOCAL_VALIDATION == true
                }
            }
            steps {
                sh '''
                echo "---" > ${LOCAL_PATH_SITE}/spellcheck_results.txt
                cd ${SRC}
                CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
                cd -
                for filename in ${CHANGED_FILES}; do
                    echo "## ${filename} ##" >> ${LOCAL_PATH_SITE}/spellcheck_results.txt
                    $HOME/.local/bin/uv run ./tools/spellcheck.py ${SRC}/${filename} >> ${LOCAL_PATH_SITE}/spellcheck_results.txt
                    echo "" >> ${LOCAL_PATH_SITE}/spellcheck_results.txt
                done
                '''
            }
        }
        stage('LLM Sumarize Content') {
            when {
                expression {
                    params.LLM_REVIEW == true && params.LOCAL_VALIDATION == true
                }
            }
            steps {
                sh '''
                echo "---" > ${LOCAL_PATH_SITE}/llm_summary.txt
                cd ${SRC}
                CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
                cd -
                for filename in ${CHANGED_FILES}; do
                    echo "## ${filename} ##" >> ${LOCAL_PATH_SITE}/llm_summary.txt
                    PYTHONPATH=/home/jenkins/agent/workspace/blog_builder
                    $HOME/.local/bin/uv run tools/llm_check.py ${SRC}/${filename} >> ${LOCAL_PATH_SITE}/llm_summary.txt
                    echo "" >> ${LOCAL_PATH_SITE}/llm_summary.txt
                done
                '''
            }
        }
        stage('Promote Release') {

            when {
                expression {
                    params.LOCAL_VALIDATION == true
                }
            }
            options {
                timeout time: 7, unit: 'MINUTES'
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
                catchError (buildResult: 'UNSTABLE', stageResult: 'FAILURE', message: 'Failed to update fallback page'){
                    script {
                        if (!fileExists("/home/jenkins/agent/workspace/${SITE_PAGES}")) {
                            sh '''
                            cd ..
                            git clone ${SITE_PAGES_URL}
                            cp -r ${SITE_DIR}/* ${SITE_PAGES}
                            cd  ${SITE_PAGES}
                            git add -A
                            git commit -am "$(date +'%Y-%m-%d %H:%M:%S')"
                            git push origin
                            '''
                        } else {
                            sh '''
                            echo "Pages is already present"
                            cd ..
                            cd ${SITE_PAGES}
                            git pull
                            cd ..
                            cp -r ${SITE_DIR}/* ${SITE_PAGES}
                            cd  ${SITE_PAGES}
                            git add -A
                            git commit -am "$(date +'%Y-%m-%d %H:%M:%S')"
                            git push origin
                            '''
                        }
                    }
                }
            }
        }
    }
    post {
        aborted {
            sh """
            echo 'Rolling back local changes'
            cp -r ../${STABLE}/${SITE_DIR} ${LOCAL_PATH_ROOT}
            """
        }
        failure {
            echo 'Upon failure you should clean repositories for the next run!'
            cleanWs()
        }
        cleanup {
            script {
                if (params.CLEAN_REPOSITORIES) {
                    dir("../${SOURCE}") { deleteDir() }
                    dir("../${SITE_DIR}") { deleteDir() }
                    dir("../${SITE_PAGES}") { deleteDir() }
                    dir("../${STABLE}") { deleteDir() }
                }
            }
        }
    }
}
