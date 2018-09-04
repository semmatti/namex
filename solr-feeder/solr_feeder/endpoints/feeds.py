
import logging

import flask
import flask_restplus

from solr_feeder.models import completed_nr
from solr_feeder import solr


__all__ = ['api']


api = flask_restplus.Namespace('Feeds', description='Feed updates from legacy databases')


# Feed the cores with the data corresponding to the posted corporation number.
@api.route('/corporations')
class _Corporations(flask_restplus.Resource):
    @staticmethod
    def post():
        return {'message': 'Okie dokie'}, 200


# Feed the cores with the data corresponding to the posted name request number.
@api.route('/names')
class _Names(flask_restplus.Resource):
    name_request_number_model = api.model(
        'Name Request Number', {'nameRequestNumber': flask_restplus.fields.String('Name Request Number')})

    @api.expect(name_request_number_model)
    def post(self):
        logging.debug('request raw data: {}'.format(flask.request.data))
        request_json = flask.request.get_json()
        if not request_json or 'nameRequestNumber' not in request_json:
            return {'message': 'Required parameter "nameRequestNumber" not defined'}, 400

        name_request_number = request_json['nameRequestNumber']
        results = completed_nr.CompletedNr.find(name_request_number)
        if not results:
            logging.info('Names lookup of "{}" failed'.format(name_request_number))

            return {'message': 'Unknown "nameRequestNumber" of "{}"'.format(name_request_number)}, 404

        for name_instance in results:
            json = completed_nr.CompletedNrSchema().dump(name_instance).data
            logging.info('Names lookup of "{}-{}" succeeded'.format(name_request_number, json['choice_number']))

            # Alter the data to conform to what the names core is expecting.
            #
            # names: SELECT nr_num || '-' || choice_number AS id, name_instance_id, choice_number, corp_num, name,
            # nr_num, request_id, submit_count, request_type_cd, name_id, start_event_id, name_state_type_cd
            names_json = _convert_json_none_to_empty_string({
                'id': json['nr_num'] + '-' + str(json['choice_number']),
                'name_instance_id': json['name_instance_id'],
                'choice_number': json['choice_number'],
                'corp_num': json['corp_num'],
                'name': json['name'],
                'nr_num': json['nr_num'],
                'request_id': json['request_id'],
                'request_type_cd': json['request_type_cd'],
                'name_id': json['name_id'],
                'start_event_id': json['start_event_id'],
                'name_state_type_cd': json['name_state_type_cd']
            })

            # Update the names core. In the case that one update succeeds and subsequent updates fail, the cores will be
            # inconsistent. However, the caller will receive a non-200 response, and will retry all updates at a later
            # time. The core data will eventually be consistent.
            error_response = solr.update_core('names', names_json)
            if error_response:
                return {'message': error_response['message']}, error_response['status_code']

            # The possible.conflicts core only wants the states of 'A' and 'C'.
            if json['name_state_type_cd'] is 'A' or json['name_state_type_cd'] is 'C':
                # Alter the data to conform to what the Solr core is expecting. We should create new views that only
                # return the data that is needed.
                #
                # possible.conflicts: SELECT nr_num AS id, name, name_state_type_cd AS state_type_cd, 'NR' AS source
                possible_conflicts_json = _convert_json_none_to_empty_string({
                    'id': json['nr_num'],
                    'name': json['name'],
                    'state_type_cd': json['name_state_type_cd'],
                    'source': 'NR'
                })

                error_response = solr.update_core('possible.conflicts', possible_conflicts_json)
                if error_response:
                    return {'message': error_response['message']}, error_response['status_code']

        return {'message': 'Solr cores updated'}, 200


# If we get null values from the database, convert them from None to ''.
def _convert_json_none_to_empty_string(json: dict) -> dict:
    for key in json.keys():
        if not json[key]:
            json[key] = ''

    return json
