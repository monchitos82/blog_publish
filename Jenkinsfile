pipeline {
    agent { label 'python' }
    environment {
        // build specifics
        ACCOUNT = "ramongarciamx"
        GIT_URL = "ssh://git@codeberg.org/${ACCOUNT}"
        SOURCE = "rgarciamx"
        TRACKING = "https://${ACCOUNT}.goatcounter.com"
        // project specifics
        BASE_URL = "https://${ACCOUNT}.neocities.org"
        DEST = "./site"
        SRC = "./${SOURCE}"
        YEAR_LOOKBACK = 1
        INDEX_PAGES = "index, about, notes"
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
    }
    stages {
        stage('Setup Environment') {
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
        stage('Setup Sources') {
            steps {
                script {
                    if (params.CLEAN_REPOSITORIES) {
                        dir("${SOURCE}") { deleteDir() }
                        dir("site") { deleteDir() }
                        sh '''
                            git clone ${GIT_URL}/${SOURCE}
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
                            git clone ${GIT_URL}/${SOURCE}
                            '''
                        }
                    }
                }
            }

        }
        stage('Build') {
            steps {
                sh '''
                    mkdir -p ./site
                    $HOME/.local/bin/uv run build_blog.py
                '''
            }

        }
        stage('Publish Local') {
            steps {
                sh """
                mkdir -p /opt/deploy
                mkdir -p ./last
                cp -r /opt/deploy ./last
                cp -r ./site /opt/deploy/
                find /opt/deploy/site -type f -exec sed -i 's|${BASE_URL}|http://127.0.0.1:2080/site|g' {} +
                find /opt/deploy/site -type f -exec sed -i 's|${TRACKING}|#|g' {} +
                """
            }
        }
        stage('Promote release') {
            
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

        stage('Publish') {
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
            cp -r ./last/* /opt/deploy/
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
