import os, sys
import pandas as pd
import config
from pcntoolkit.normative_model.norm_base import NormBase
from pcntoolkit.normative_model.norm_factory import load_normative_model
from pcntoolkit.dataio.norm_data import NormData
from pcntoolkit.util.runner import Runner
import copy


def main():
    root_dir = config.project_dir
    model_name, data_type, session_id, model_dir, alg, email_address = sys.argv[2:]
    model_path = os.path.join(root_dir, model_dir, data_type, model_name)
    session_path = os.path.join(root_dir, "sessions", session_id) + "/"
    transfer_fit_data = pd.read_pickle(os.path.join(session_path, "adapt.pkl"))
    transfer_predict_data = pd.read_pickle(os.path.join(session_path, "test.pkl"))

    nm: NormBase = load_normative_model(model_path)

    # Create the training and prediction data   
    train_data = NormData.from_dataframe(
        "transfer_fit",
        transfer_fit_data,
        covariates=nm.covariates,
        response_vars=nm.response_vars,
        batch_effect_dims=list(nm.unique_batch_effects.keys()),
    )
    predict_data = NormData.from_dataframe(
        "transfer_predict",
        transfer_predict_data,
        covariates=nm.covariates,
        response_vars=nm.response_vars,
        batch_effect_dims=list(nm.unique_batch_effects.keys()),
    )

    # Create a runner to take care of the paralellization
    runner = Runner(
        cross_validation=False,
        parallelize=True,
        job_type="slurm",
        n_jobs=3,
        n_cores=4,
        python_path=config.python_path,
        time_limit="48:00:00",
        memory="4gb",
        log_dir=os.path.join(session_path, "log_dir"),
        temp_dir=os.path.join(session_path, "temp_dir"),
    )

    # Override the save directory so all the models and results are saved in the session directory
    nm.set_save_dir(os.path.join(session_path, "save_dir"))
        
    # Transfer the model to the and predict
    runner.transfer_predict(nm, train_data, predict_data)

    
    


if __name__ == "__main__":
    main()
