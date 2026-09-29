import pathlib
import pandas as pd
import sys
from datetime import datetime
from sqlalchemy import text
from Models_and_engine import insert_logs, dynamic_engine

current = pathlib.Path('.').parent.absolute()
separator = '\\' if sys.platform.startswith('win') else '/'


def replace_table_as_select(connection, table_name, select_sql):
    connection.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
    connection.execute(text(f"CREATE TABLE `{table_name}` AS {select_sql}"))


async def safe_log(user, company, websocket_id, process, message):
    try:
        await insert_logs(user, company, websocket_id, process, message)
    except Exception:
        pass


def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    upper_map = {c.upper(): c for c in df.columns}
    return df, upper_map


def get_col(df, *candidates):
    cols = {str(c).strip().upper(): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().upper()
        if key in cols:
            return cols[key]
    raise KeyError(f"None of the candidate columns were found: {candidates}. Available: {list(df.columns)}")


async def Role_analysis(output_path, company, User, WebSocketID, option=False):
    try:
        await safe_log(User, company, WebSocketID, 'Role Analysis', 'Role Analysis process started')
        print(datetime.now())

        if option:
            with dynamic_engine(company) as DB:
                with DB.begin() as connection:
                    replace_table_as_select(
                        connection,
                        f"children_permissions_{User}",
                        '''
                        SELECT `Business Process`, `Security Object Label`
                        FROM SOD_Rules
                        WHERE `Security Object Label` <> `Business Process`
                        GROUP BY `Business Process`, `Security Object Label`
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created children_permissions_{User} table')

                    replace_table_as_select(
                        connection,
                        f"Role_To_Permissions_Union_{User}",
                        f'''
                        WITH role_permissions_extended_{User} AS (
                            SELECT rp.Id, cp.`Business Process` AS `Permission`, rp.Level
                            FROM role_permissions rp
                            INNER JOIN `children_permissions_{User}` cp ON rp.Permission = cp.`Security Object Label`
                            WHERE rp.`Level` > 1
                            UNION
                            SELECT `Id`, `Permission`, `Level`
                            FROM role_permissions
                            WHERE `Level` > 1
                        )
                        SELECT `Id`, `Permission`, MAX(`Level`) AS `Level`
                        FROM role_permissions_extended_{User}
                        GROUP BY `Id`, `Permission`
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created Role_To_Permissions_Union_{User} table')

                    replace_table_as_select(
                        connection,
                        f"SOD_Rules_cleaned_{User}",
                        '''
                        SELECT
                            *,
                            `Security Object Label` AS `Permission 1`,
                            CASE
                                WHEN (
                                    CASE
                                        WHEN `Name` LIKE '% & %' THEN SUBSTRING_INDEX(`Name`, ' & ', 1)
                                        WHEN `Name` LIKE '% and %' THEN SUBSTRING_INDEX(`Name`, ' and ', 1)
                                        ELSE `Name`
                                    END
                                ) <> `Business Process` THEN
                                    CASE
                                        WHEN `Name` LIKE '% & %' THEN SUBSTRING_INDEX(`Name`, ' & ', 1)
                                        WHEN `Name` LIKE '% and %' THEN SUBSTRING_INDEX(`Name`, ' and ', 1)
                                        ELSE `Name`
                                    END
                                ELSE
                                    CASE
                                        WHEN `Name` LIKE '% & %' THEN SUBSTRING_INDEX(`Name`, ' & ', -1)
                                        WHEN `Name` LIKE '% and %' THEN SUBSTRING_INDEX(`Name`, ' and ', -1)
                                        ELSE `Name`
                                    END
                            END AS `Permission 2`
                        FROM SOD_Rules
                        WHERE `Risk Type` = 'Segregation of Duties'
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created SOD_Rules_cleaned_{User} table')

                    replace_table_as_select(
                        connection,
                        f"All_Role_Risk_{User}",
                        f'''
                        SELECT
                            r.InternalId AS `Role Id`,
                            r.Name AS `Role`,
                            sr.`Risk Id`,
                            sr.`Name` AS `Risk Name`,
                            sr.`Business Process`,
                            sr.`Security Object Type` AS `Object Type`,
                            sr.`Security Object Name` AS `Object Name`,
                            sr.`Security Object Label` AS `Object Label`,
                            CASE
                                WHEN rp1.`Level` = 0 THEN 'None'
                                WHEN rp1.`Level` = 1 THEN 'View'
                                WHEN rp1.`Level` = 2 THEN 'Create'
                                WHEN rp1.`Level` = 3 THEN 'Edit'
                                ELSE 'Full'
                            END AS `Access Type`,
                            sr.`Description` AS `Risk Description`,
                            sr.`Risk Type`,
                            sr.Product,
                            sr.`Risk Level`,
                            sr.`Default Mitigation`,
                            sr.`Business Cycle`,
                            sr.`Policy`,
                            sr.`Is Default Ruleset`,
                            sr.`Permission 1`,
                            sr.`Permission 2`
                        FROM `SOD_Rules_cleaned_{User}` sr
                        JOIN `Role_To_Permissions_Union_{User}` rp1 ON sr.`Permission 1` = rp1.Permission
                        JOIN `Role_To_Permissions_Union_{User}` rp2 ON sr.`Permission 2` = rp2.Permission
                        JOIN `roles_{User}` r ON r.InternalId = rp1.Id
                        WHERE sr.Enabled = TRUE AND rp1.Id = rp2.Id AND rp1.Level > 1 AND rp2.Level > 1
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created All_Role_Risk_{User} table')

                    replace_table_as_select(
                        connection,
                        f"Individual_Role_Risk_Detailed_{User}",
                        f'''
                        SELECT arr.*
                        FROM `All_Role_Risk_{User}` arr
                        WHERE arr.`Object Label` IN (
                            SELECT `Permission`
                            FROM `role_permissions_{User}`
                            WHERE `Id` = arr.`Role Id` AND `Level` > 1
                            GROUP BY `Id`, `Permission`
                        )
                        ORDER BY arr.`Role` ASC, arr.`Risk Name` ASC, arr.`Business Process` ASC
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created Individual_Role_Risk_Detailed_{User} table')

                    replace_table_as_select(
                        connection,
                        f"Individual_Role_Risk_{User}",
                        f'''
                        SELECT d.*
                        FROM `Individual_Role_Risk_Detailed_{User}` d
                        INNER JOIN (
                            SELECT `Role Id`, `Risk Id`, MIN(`Object Label`) AS `Object Label`
                            FROM `Individual_Role_Risk_Detailed_{User}`
                            GROUP BY `Role Id`, `Risk Id`
                        ) x
                            ON d.`Role Id` = x.`Role Id`
                            AND d.`Risk Id` = x.`Risk Id`
                            AND d.`Object Label` = x.`Object Label`
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created Individual_Role_Risk_{User} table')

                    replace_table_as_select(
                        connection,
                        f"user_subsidiary_role_permissions_{User}",
                        f'''
                        WITH all_user_permissions_{User} AS (
                            SELECT DISTINCT
                                er.UserId,
                                er.Email,
                                CASE
                                    WHEN rs.Subsidiary IS NULL THEN er.SubsidiaryId
                                    ELSE rs.Subsidiary
                                END AS `SubsidiaryId`,
                                er.RoleId,
                                rp.Permission,
                                rp.Level
                            FROM `employee_roles_{User}` er
                            LEFT JOIN `role_subsidiaries_{User}` rs ON rs.Id = er.RoleId
                            INNER JOIN `role_permissions_{User}` rp ON rp.Id = er.RoleId
                        )
                        SELECT * FROM all_user_permissions_{User}
                        WHERE all_user_permissions_{User}.Level > 1
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created user_subsidiary_role_permissions_{User} table')

                    replace_table_as_select(
                        connection,
                        f"global_permissions_{User}",
                        f'''
                        SELECT egp.Email, egp.Permission, egp.LevelId, -1 AS RoleId
                        FROM `employee_global_permissions_{User}` egp
                        '''
                    )
                    await safe_log(User, company, WebSocketID, 'Role Analysis', f'Created global_permissions_{User} table')

                    replace_table_as_select(
                        connection,
                        f"user_subsidiary_role_permissions_global_{User}",
                        f'''SELECT * FROM `user_subsidiary_role_permissions_{User}`'''
                    )

                    connection.execute(text(f'''
                        INSERT INTO `user_subsidiary_role_permissions_global_{User}` (UserId, Email, SubsidiaryId, RoleId, Permission, Level)
                        SELECT
                            usrp.UserId,
                            egp.Email,
                            usrp.SubsidiaryId,
                            egp.RoleId,
                            egp.Permission,
                            egp.LevelId
                        FROM `global_permissions_{User}` egp
                        JOIN (
                            SELECT DISTINCT UserId, Email, SubsidiaryId
                            FROM `user_subsidiary_role_permissions_{User}`
                        ) usrp ON egp.Email = usrp.Email
                        WHERE egp.RoleId = -1
                    '''))

                    replace_table_as_select(
                        connection,
                        f"user_subsidiary_role_permissions_global_union_{User}",
                        f'''
                        WITH unioned AS (
                            SELECT
                                usrpg.UserId,
                                usrpg.Email,
                                usrpg.SubsidiaryId,
                                usrpg.RoleId,
                                cp.`Business Process` AS `Permission`,
                                usrpg.Level
                            FROM `user_subsidiary_role_permissions_global_{User}` usrpg
                            INNER JOIN `children_permissions_{User}` cp ON usrpg.Permission = cp.`Security Object Label`
                            UNION ALL
                            SELECT
                                usrpg.UserId,
                                usrpg.Email,
                                usrpg.SubsidiaryId,
                                usrpg.RoleId,
                                usrpg.`Permission`,
                                usrpg.Level
                            FROM `user_subsidiary_role_permissions_global_{User}` usrpg
                        )
                        SELECT
                            UserId,
                            Email,
                            SubsidiaryId,
                            RoleId,
                            Permission,
                            MAX(Level) AS Level
                        FROM unioned
                        GROUP BY UserId, Email, SubsidiaryId, RoleId, Permission
                        '''
                    )

                    replace_table_as_select(
                        connection,
                        f"user_subsidiary_role_permissions_global_union_final_{User}",
                        f'''SELECT * FROM `user_subsidiary_role_permissions_global_union_{User}`'''
                    )

                    connection.execute(text(f'''
                        UPDATE `user_subsidiary_role_permissions_global_union_final_{User}` usrpf
                        INNER JOIN (
                            SELECT * FROM `user_subsidiary_role_permissions_global_union_{User}`
                            WHERE RoleId = -1
                        ) gp
                            ON gp.UserId = usrpf.UserId
                            AND gp.Email = usrpf.Email
                            AND gp.SubsidiaryId = usrpf.SubsidiaryId
                            AND gp.Permission = usrpf.Permission
                        SET usrpf.Level = gp.Level
                    '''))

                sod_rules = pd.read_sql(f'SELECT * FROM `SOD_Rules_cleaned_{User}`', DB)
                user_subsidiary_role_permissions_global_union_final = pd.read_sql(
                    f'SELECT * FROM `user_subsidiary_role_permissions_global_union_final_{User}`', DB
                )
                user_subsidiary_role_permissions_global = pd.read_sql(
                    f'SELECT * FROM `user_subsidiary_role_permissions_global_{User}`', DB
                )
                employees = pd.read_sql(
                    f'''SELECT `InternalId`, `Name` AS `User Name`,
                    CASE WHEN `IsInactive` = False THEN True ELSE False END AS `User Status`
                    FROM `employees_{User}`''', DB
                )
                rules = pd.read_sql(
                    f'''SELECT `Risk Id`, `Risk Type`, `Policy`,
                    `Default Mitigation` AS `Mitigation`,
                    `Mitigation Status` AS `Mitigation Control`, `Mitigation Notes`,
                    `Product`, `Risk Level` FROM `SOD_Rules_cleaned_{User}`''', DB
                )
                subsidiaries = pd.read_sql(
                    f'''SELECT `InternalId`, `Name` AS `Company` FROM `subsidiaries_{User}`''', DB
                )
                roles = pd.read_sql(
                    f'''SELECT `InternalId`, `Name` AS `Role` FROM `roles_{User}`''', DB
                )

                user_risk_detailed, user_risk_detailed_final, user_risk = await user_risk_data_process(
                    sod_rules,
                    user_subsidiary_role_permissions_global_union_final,
                    user_subsidiary_role_permissions_global,
                    employees,
                    rules,
                    subsidiaries,
                    roles,
                    User,
                    company,
                    WebSocketID
                )

                with dynamic_engine(company) as engine:
                    user_risk_detailed.to_sql(f'user_risk_detailed_{User}', con=engine, if_exists='replace', index=False)
                    user_risk_detailed_final.to_sql(f'user_risk_detailed_final_{User}', con=engine, if_exists='replace', index=False)
                    user_risk.to_sql(f'user_risk_final_{User}', con=engine, if_exists='replace', index=False)

        with dynamic_engine(company) as engine:
            with pd.ExcelWriter(output_path) as writer:
                pd.read_sql(
                    f'''SELECT * FROM `Individual_Role_Risk_Detailed_{User}`
                    ORDER BY `Role` ASC, `Risk Name` ASC, `Business Process` ASC''', engine
                ).to_excel(writer, sheet_name='Individual Role Risk Detailed', index=False)

                pd.read_sql(
                    f'''SELECT * FROM `Individual_Role_Risk_{User}`
                    ORDER BY `Role` ASC, `Risk Name` ASC, `Business Process` ASC''', engine
                ).to_excel(writer, sheet_name='Individual Role Risk', index=False)

                pd.read_sql(
                    f'''SELECT * FROM `user_risk_detailed_final_{User}`
                    ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Security Object` ASC''', engine
                ).to_excel(writer, sheet_name='User Risk Detailed', index=False)

                pd.read_sql(
                    f'''SELECT * FROM `user_risk_final_{User}`
                    ORDER BY `User Name` ASC, `Risk Name` ASC''', engine
                ).to_excel(writer, sheet_name='User Risk', index=False)

        await safe_log(User, company, WebSocketID, 'Role Analysis', f'{output_path.split(separator)[-1]} file returned')
        return output_path

    except Exception as e:
        print(e)
        await safe_log(User, company, WebSocketID, 'Role Analysis', f'An error ocurred: {e}')
        raise


async def user_risk_data_process(sod_rules, usr_permissions, user_permissions_global, employees, rules, subsidiaries, roles, UserID, Company, WebSocketID):
    await safe_log(UserID, Company, WebSocketID, 'user_risk_data_process', 'Looking for all user risk')
    print(f'Looking for all user risk: {datetime.now()}')

    sod_rules, _ = normalize_columns(sod_rules)
    usr_permissions, _ = normalize_columns(usr_permissions)
    user_permissions_global, _ = normalize_columns(user_permissions_global)
    employees, _ = normalize_columns(employees)
    rules, _ = normalize_columns(rules)
    subsidiaries, _ = normalize_columns(subsidiaries)
    roles, _ = normalize_columns(roles)

    enabled_col = get_col(sod_rules, 'ENABLED', 'Enabled')
    risk_id_col = get_col(sod_rules, 'Risk Id')
    risk_name_col = get_col(sod_rules, 'NAME', 'Name', 'Risk Name')
    desc_col = get_col(sod_rules, 'DESCRIPTION', 'Description')
    cycle_col = get_col(sod_rules, 'BUSINESS CYCLE', 'Business Cycle')
    process_col = get_col(sod_rules, 'BUSINESS PROCESS', 'Business Process')
    obj_label_col = get_col(sod_rules, 'SECURITY OBJECT LABEL', 'Security Object Label')
    obj_name_col = get_col(sod_rules, 'SECURITY OBJECT NAME', 'Security Object Name')
    obj_type_col = get_col(sod_rules, 'SECURITY OBJECT TYPE', 'Security Object Type')
    p1_col = get_col(sod_rules, 'Permission 1')
    p2_col = get_col(sod_rules, 'Permission 2')

    enabled_rules = sod_rules[sod_rules[enabled_col].isin([1, True, '1', 'True', 'TRUE'])]
    valid_permissions = usr_permissions[usr_permissions[get_col(usr_permissions, 'Level')] > 1]
    all_user_risk = []

    for _, rule in enabled_rules.iterrows():
        up1_filtered = valid_permissions[valid_permissions[get_col(valid_permissions, 'Permission')] == rule[p1_col]]
        for _, up1 in up1_filtered.iterrows():
            up2_filtered = valid_permissions[
                (valid_permissions[get_col(valid_permissions, 'Permission')] == rule[p2_col]) &
                (valid_permissions[get_col(valid_permissions, 'UserId')] == up1[get_col(valid_permissions, 'UserId')]) &
                (valid_permissions[get_col(valid_permissions, 'SubsidiaryId')] == up1[get_col(valid_permissions, 'SubsidiaryId')])
            ]
            for _, up2 in up2_filtered.iterrows():
                all_user_risk.append({
                    'UserId': up1[get_col(valid_permissions, 'UserId')],
                    'Email': up1[get_col(valid_permissions, 'Email')],
                    'SubsidiaryId': up1[get_col(valid_permissions, 'SubsidiaryId')],
                    'RoleId 1': up1[get_col(valid_permissions, 'RoleId')],
                    'Risk Id': rule[risk_id_col],
                    'Risk Name': rule[risk_name_col],
                    'Description': rule[desc_col],
                    'Business Cycle': rule[cycle_col],
                    'Business Process': rule[process_col],
                    'Security Object Label': rule[obj_label_col],
                    'Security Object Name': rule[obj_name_col],
                    'Security Object Type': rule[obj_type_col],
                    'Permission 1': rule[p1_col],
                    'Permission 2': rule[p2_col],
                    'Level': min(up1[get_col(valid_permissions, 'Level')], up2[get_col(valid_permissions, 'Level')])
                })

    await safe_log(UserID, Company, WebSocketID, 'user_risk_data_process', 'All user risk found')
    print(f'All user risk found: {datetime.now()}')

    all_user_risk = pd.DataFrame(all_user_risk)
    if all_user_risk.empty:
        filtered_risk = pd.DataFrame(columns=[
            'UserId', 'Email', 'SubsidiaryId', 'RoleId 1', 'Risk Id', 'Risk Name', 'Description',
            'Business Cycle', 'Business Process', 'Security Object Label', 'Security Object Name',
            'Security Object Type', 'Permission 1', 'Permission 2', 'Level'
        ])
    else:
        all_user_risk = all_user_risk.drop_duplicates().to_dict('records')
        filtered_risk = []
        for risk in all_user_risk:
            if not user_permissions_global[
                (user_permissions_global[get_col(user_permissions_global, 'UserId')] == risk['UserId']) &
                (user_permissions_global[get_col(user_permissions_global, 'SubsidiaryId')] == risk['SubsidiaryId']) &
                (user_permissions_global[get_col(user_permissions_global, 'RoleId')] == risk['RoleId 1']) &
                (user_permissions_global[get_col(user_permissions_global, 'Permission')] == risk['Security Object Label']) &
                (user_permissions_global[get_col(user_permissions_global, 'Level')] > 1)
            ].empty:
                filtered_risk.append(risk)

        filtered_risk = pd.DataFrame(filtered_risk)
        if not filtered_risk.empty:
            filtered_risk = filtered_risk.drop_duplicates(subset=['UserId', 'SubsidiaryId', 'RoleId 1', 'Risk Id', 'Security Object Label'])
            filtered_risk = filtered_risk.sort_values(by=['Risk Name', 'Security Object Label'])
            filtered_risk_copy = filtered_risk.copy()
            filtered_risk_merged = pd.merge(
                filtered_risk,
                filtered_risk_copy,
                on=[
                    'UserId', 'Email', 'SubsidiaryId', 'Risk Id', 'Risk Name',
                    'Description', 'Business Cycle', 'Business Process',
                    'Security Object Label', 'Security Object Name', 'Security Object Type',
                    'Permission 1', 'Permission 2'
                ],
                how='left',
                suffixes=('', '_copy')
            )
            filtered_risk_merged = filtered_risk_merged[
                (filtered_risk_merged['RoleId 1'] != -1) &
                (filtered_risk_merged['RoleId 1_copy'] == -1)
            ]
            columns = [
                'UserId', 'Email', 'SubsidiaryId', 'RoleId 1', 'Risk Id', 'Risk Name', 'Description',
                'Business Cycle', 'Business Process', 'Security Object Label', 'Security Object Name',
                'Security Object Type', 'Permission 1', 'Permission 2', 'Level'
            ]
            filtered_risk = filtered_risk[
                ~filtered_risk[columns].apply(tuple, axis=1).isin(filtered_risk_merged[columns].apply(tuple, axis=1))
            ]

    if filtered_risk.empty:
        risk_final = pd.DataFrame(columns=[
            'User ID', 'User Name', 'User Type', 'User Status', 'Risk ID', 'Risk Name', 'Risk Type',
            'Business Cycle', 'Risk Level', 'Policy', 'Risk Description', 'Status', 'Mitigation',
            'Mitigation Control', 'Mitigation Notes', 'Asigned User', 'Company', 'Company ID',
            'Business Process', 'Group Name', 'Group Type', 'Security Object Product', 'Security Object',
            'Security Object Type', 'Access Type', 'Role'
        ])
        user_risk = pd.DataFrame(columns=[
            'User Name', 'Risk Name', 'Risk Description', 'Risk Level', 'Risk Type', 'Status', 'Company', 'Company ID', 'Asigned User'
        ])
        return filtered_risk, risk_final, user_risk

    risk_final = filtered_risk.merge(employees, left_on='UserId', right_on=get_col(employees, 'InternalId'), how='inner')
    risk_final = risk_final.merge(rules, on='Risk Id', how='inner')
    risk_final = risk_final.merge(subsidiaries, left_on='SubsidiaryId', right_on=get_col(subsidiaries, 'InternalId'), how='inner')
    risk_final = risk_final.merge(roles, left_on='RoleId 1', right_on=get_col(roles, 'InternalId'), how='left')

    drop_cols = [c for c in ['Permission 1', 'Permission 2', 'InternalId_x', 'InternalId_y', 'InternalId'] if c in risk_final.columns]
    risk_final = risk_final.drop(columns=drop_cols).drop_duplicates()
    risk_final = risk_final.rename(columns={
        'Email': 'User ID',
        'SubsidiaryId': 'Company ID',
        'Risk Id': 'Risk ID',
        'Description': 'Risk Description',
        'Product': 'Security Object Product',
        'Security Object Label': 'Security Object',
        'Level': 'Access Type'
    })

    risk_final['User Type'] = None
    risk_final['Access Type'] = risk_final['Access Type'].map({0: 'None', 1: 'View', 2: 'Create', 3: 'Edit', 4: 'Full'}).fillna('Full')
    risk_final['Role'] = risk_final['Role'].apply(lambda x: 'GLOBAL PERMISSIONS' if pd.isna(x) else x)
    risk_final['Group Name'] = None
    risk_final['Group Type'] = None
    risk_final['Status'] = None
    risk_final['Asigned User'] = None
    risk_final = risk_final.drop(columns=['RoleId 1'])
    risk_final = risk_final[[
        'UserId', 'User ID', 'User Name', 'User Type', 'User Status', 'Risk ID', 'Risk Name', 'Risk Type',
        'Business Cycle', 'Risk Level', 'Policy', 'Risk Description', 'Status', 'Mitigation',
        'Mitigation Control', 'Mitigation Notes', 'Asigned User', 'Company', 'Company ID',
        'Business Process', 'Group Name', 'Group Type', 'Security Object Product', 'Security Object',
        'Security Object Type', 'Access Type', 'Role'
    ]]
    risk_final = risk_final.sort_values(by=['User ID', 'User Name', 'Risk Name', 'Security Object'])

    user_risk = risk_final.drop_duplicates(subset=['UserId', 'User ID', 'Company ID', 'Risk Name'])
    user_risk = user_risk.drop(columns=[
        'User ID', 'User Type', 'User Status', 'Risk ID', 'Business Cycle', 'Policy', 'Mitigation',
        'Mitigation Control', 'Mitigation Notes', 'Business Process', 'Group Name', 'Group Type',
        'Security Object Product', 'Security Object', 'Security Object Type', 'Access Type', 'Role'
    ])
    user_risk = user_risk[[
        'UserId', 'User Name', 'Risk Name', 'Risk Description', 'Risk Level', 'Risk Type',
        'Status', 'Company', 'Company ID', 'Asigned User'
    ]].sort_values(by=['User Name', 'Risk Name'])

    risk_final = risk_final.drop(columns=['UserId'])
    user_risk = user_risk.drop(columns=['UserId'])
    return filtered_risk, risk_final, user_risk

