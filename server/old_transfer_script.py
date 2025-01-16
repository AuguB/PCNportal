#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14, 2022

@author: Pieter Barkema

This script has partially been adapted from apply_normative_models.py (author: Saige Rutherford) and transfer_hbr_models.py (author: Seyed Mostafa Kia).

The purpose of this script is to act as frontend for normative.transfer for all algorithms in an automated way.
The script can be used by an online interface to feed in arguments to do transfer learning with pre-trained models.
Finally, the script facilitates uploading and sharing results.

"""


def transfer_normative_models():
    """

    Transfer learning script that is compatible with an online user interface.
    The script prepares and preprocesses data, and sets parameters to perform
    parallelized computation jobs.

    Parameters
    ----------
    root_dir : string
        The (currently hardcoded) path to the main project directory.
    model_name : string
        The normative model chosen by the user. Name contains algorithm, training sample,
        n collection sites.
    data_type : string
        The data type chosen by the user to do normative modelling with.
    session_id : string [converted from uuid]
        Unique session ID corresponding to the client side ID.
    algorithm : string [BLR or HBR]
        Normative modelling algorithm.
    email_address : string
        The email address to sent the session results to.

    Returns
    -------
    None. It produces modelling results, and uploads and emails them to the user.

    """

    import os, sys
    import numpy as np
    import pandas as pd
    import pickle
    import json
    import config
    import pcntoolkit as ptk
    from package_and_send_surfdrive import send_results
    from pcntoolkit.util.utils import create_design_matrix

    # Read in website input.
    root_dir = config.project_dir
    model_name = sys.argv[2]
    data_type = sys.argv[3]
    session_id = sys.argv[4]

    # untested models or not
    model_dir = sys.argv[5]
    alg = model_name.split("_")[0]
    email_address = sys.argv[6]
    model_info_path = os.path.join(root_dir, model_dir, data_type, model_name)
    model_path = os.path.join(root_dir, model_dir, data_type, model_name, "Models")

    # Create session directory, and read in data.
    session_path = os.path.join(root_dir, "sessions", session_id) + "/"
    print(f"{session_path}")
    if not os.path.isdir(session_path):
        os.mkdir(session_path)
    os.chdir(session_path)
    df_te = pd.read_pickle(os.path.join(session_path, "test.pkl"))
    df_ad = pd.read_pickle(os.path.join(session_path, "adapt.pkl"))

    # Site enumeration.
    sites = np.unique(df_te["site"])

    df_te["sitenum"] = np.nan
    for i, s in enumerate(sites):
        df_te["sitenum"].loc[df_te["site"] == s] = int(i)
    df_ad["sitenum"] = np.nan
    for i, s in enumerate(sites):
        df_ad["sitenum"].loc[df_ad["site"] == s] = int(i)

    # Extract a list of unique site ids for test and adaptation.
    site_names = "site_ids.txt"
    with open(os.path.join(model_info_path, site_names)) as f:
        site_ids_tr = f.read().splitlines()
    site_ids_te = sorted(set(df_te["site"].to_list()))

    # Read in, prepare and save test brain features.
    with open(os.path.join(model_info_path, "idp_ids.txt")) as f:
        idps = f.read().splitlines()
    # Sample for determining batch sizes.
    testing_sample = len(df_te.columns.intersection(set(idps)))
    # Only extract available columns.
    y_te = df_te[df_te.columns.intersection(set(idps))].to_numpy(dtype=float)
    resp_file_te = os.path.join(session_path, "resp_te.pkl")
    with open(resp_file_te, "wb") as file:
        pickle.dump(pd.DataFrame(y_te), file)

    # BLR and HBR have slightly different data input.
    covs_file = open(os.path.join(model_info_path, "covariates.txt"), "r")
    cols_cov = covs_file.read().splitlines()
    if alg == "BLR":
        # cols_cov = ['age', 'sex']
        # Limits for cubic B-spline basis .
        xmin = -5
        xmax = 110
        # Prepare test covariates BLR.
        with open(os.path.join(model_info_path, site_names)) as f:
            site_ids_tr = f.read().splitlines()
        x_te = create_design_matrix(
            df_te[cols_cov],
            site_ids=df_te["site"],
            all_sites=site_ids_tr,
            basis="bspline",
            xmin=xmin,
            xmax=xmax,
        )
    # Sex is a site effect in HBR, so no covariate.
    elif alg == "HBR":
        # cols_cov = ['age']
        # Prepare test covariates HBR.
        x_te = df_te[cols_cov].to_numpy(dtype=float)

    cov_file_te = os.path.join(session_path, "cov_bspline_te.pkl")
    with open(cov_file_te, "wb") as file:
        pickle.dump(pd.DataFrame(x_te), file)

    cov_file_ad = os.path.join(session_path, "cov_bspline_ad.pkl")
    resp_file_ad = os.path.join(session_path, "resp_ad.pkl")
    sitenum_file_te = os.path.join(session_path, "sitenum_te.pkl")
    sitenum_file_ad = os.path.join(session_path, "sitenum_ad.pkl")
    output_path = os.path.join(session_path, "Transfer/")

    # Adaptation covariates for BLR.
    print("colscov:", cols_cov)
    if alg == "BLR":
        x_ad = create_design_matrix(
            df_ad[cols_cov],
            site_ids=df_ad["site"],
            all_sites=site_ids_tr,
            basis="bspline",
            xmin=xmin,
            xmax=xmax,
        )

    # Adaptation covariates for HBR.
    elif alg == "HBR":
        x_ad = df_ad[cols_cov].to_numpy(dtype=float)

    # Save adaptation covariates.
    with open(cov_file_ad, "wb") as file:
        pickle.dump(pd.DataFrame(x_ad), file)

    # Save adaptation brain features.
    # Only select presented features that model has been trained on.
    y_ad = df_ad[df_ad.columns.intersection(set(idps))].to_numpy(dtype=float)
    with open(resp_file_ad, "wb") as file:
        pickle.dump(pd.DataFrame(y_ad), file)

    # Test and adaptation batch effects.
    batch_effects_file = open(os.path.join(model_info_path, "batch_effects.txt"), "r")
    cols_batch_effects = batch_effects_file.read().splitlines()
    cols_batch_effects = ["sitenum" if x == "site" else x for x in cols_batch_effects]
    if len(cols_batch_effects) == 1:
        cols_batch_effects = cols_batch_effects[0]
    print("colsbe:", cols_batch_effects)
    site_num_te = df_te[cols_batch_effects]
    site_num_ad = df_ad[cols_batch_effects]

    with open(sitenum_file_ad, "wb") as file:
        pickle.dump(site_num_ad, file)
    with open(sitenum_file_te, "wb") as file:
        pickle.dump(site_num_te, file)

    # If the model has seen all presented sites, transfer is not necessary.
    if all(elem in site_ids_tr for elem in site_ids_te):
        yhat_te, s2_te, Z = ptk.normative.predict(
            cov_file_te,
            inputsuffix="fit",
            alg=alg,
            respfile=resp_file_te,
            model_path=model_path,
            tsbefile=sitenum_file_te,
            trbefile=sitenum_file_ad,
            cluster_spec="slurm",
        )  # os.path.join(root_dir,'Models'))
    else:
        # Prepare parameters for parallelized normative modelling.
        log_dir = os.path.join(session_path, "logs/")
        outputsuffix = "_transfer"
        inputsuffix = "fit"

        # Creates many small batches for quicker processing.
        batch_size = (
            int(testing_sample ** (1 / 3)) if int(testing_sample ** (1 / 3)) >= 1 else 1
        )
        outputsuffix = "_transfer"
        try:
            memory = config.memory
        except ValueError:
            memory = "4gb"
        try:
            duration = config.duration
        except ValueError:
            duration = "48:00:00"
        python_path = config.python_path

        # Set default configuration
        inscaler = "None"
        outscaler = "None"
        method = "linear"  #'bspline' # 'linear' 'polynomial'

        likelihood = "Normal"
        init = "jitter+adapt_diag"

        random_intercept = "True"
        random_slope = "True"
        random_noise = "True"
        random_slope_sigma = "False"
        if model_name in ["HBR_HOM"]:
            hetero_noise = "False"
        else:
            hetero_noise = "True"

        # Override defaults if a model config file is found
        cfg_file = os.path.join(model_info_path, "config.json")
        if os.path.exists(cfg_file):
            with open(cfg_file, "r") as f:
                cfg = json.loads(json.load(f))
            if "likelihood" in cfg.keys():
                likelihood = cfg["likelihood"]
                if likelihood != "Normal":
                    batch_size = 1
            if "model_type" in cfg.keys():
                method = cfg["model_type"]
            if "random_slope_sigma" in cfg:
                random_slope_sigma = cfg["random_slope_sigma"]
            if "inscaler" in cfg.keys():
                inscaler = cfg["inscaler"]
            if "outscaler" in cfg.keys():
                outscaler = cfg["outscaler"]
            if "init" in cfg.keys():
                init = cfg["init"]

        # Setting up the Paths and Model.
        job_name = model_name + "_" + method
        log_dir = session_path + "/log/"
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        if not os.path.isdir(output_path):
            os.mkdir(output_path)

        # Signifies when jobs are done, for automatic management of computation jobs.
        count_jobsdone = "True"

        # PCNtoolkit transfer configuration.
        ptk.normative_parallel.execute_nm(
            session_path,
            python_path,
            "Transfer_" + job_name,
            cov_file_ad,
            resp_file_ad,
            batch_size,
            memory,
            duration,
            func="transfer",
            alg=alg,
            binary=True,
            trbefile=sitenum_file_ad,
            model_type=method,
            random_intercept=random_intercept,
            random_slope=random_slope,
            random_noise=random_noise,
            hetero_noise=hetero_noise,
            savemodel="True",
            outputsuffix=outputsuffix,
            inputsuffix=inputsuffix,
            n_samples="1000",
            inscaler=inscaler,
            outscaler=outscaler,
            testcovfile_path=cov_file_te,
            testrespfile_path=resp_file_te,
            tsbefile=sitenum_file_te,
            output_path=output_path,
            model_path=model_path,
            log_path=log_dir,
            count_jobsdone=count_jobsdone,
            likelihood=likelihood,
            random_slope_sigma=random_slope_sigma,
            cluster_spec="slurm",
        )

        # Loop that only finishes when models are succesfully completed.
        complete = False
        while complete == False:
            await_jobs(session_path, log_dir)

            # Returns true when all jobs were succesful.
            print("Start collecting...")
            complete = ptk.normative_parallel.collect_nm(
                session_path,
                "Transfer_" + job_name,
                func="transfer",
                collect=True,
                binary=True,
                batch_size=batch_size,
                outputsuffix=outputsuffix,
            )

            if complete == True:
                break

            # Rerun failed jobs.
            print("Start rerunning...")
            ptk.normative_parallel.rerun_nm(
                session_path, log_dir, memory, duration, binary=True
            )

    # Communicate results with Gmail and SURFdrive API.
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if ".e" in file or ".o" in file:
                os.chmod(os.path.join(root, file), 0o664)

    send_results(session_id, email_address)


def await_jobs(session_path, log_dir):
    """

    This waiter loop checks in on the parallelized computations.
    It ends when all the jobs are done, or when the time limit is reached.
    The loop is necessary to prevent premature collection of results.

    Parameters
    ----------
    session_path : string
        The server side path to the current session directory.
    log_dir : string
        The path to the qsub logs, where it checks if jobs are completed.

    Returns
    -------
    None.

    """

    import time, glob

    jobs_done = False
    # Maximum time limit to wait, before trying to collect results.
    max_time = 2 * 86400  # = 24 hours (was 16000)

    # Prevents unnecessary computations.
    sleep_time = 20
    elapsed_time = 0

    batch_dir = glob.glob(session_path + "batch_*")
    number_of_batches = len(batch_dir)
    while jobs_done == False:
        print(f"{number_of_batches=}, {jobs_done=}")

        # Checks if all jobs have been completed.
        done_count = len(glob.glob(log_dir + "*.jobsdone"))
        if done_count >= number_of_batches:
            break

        time.sleep(sleep_time)
        elapsed_time += sleep_time
        # Break out of loop to check for failed jobs.
        if elapsed_time > max_time:
            print("Maximum wait time elapsed.")
            break
    print("All", done_count, " out of ", number_of_batches, " jobs done!")


transfer_normative_models()
