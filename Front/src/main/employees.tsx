import React from 'react';
import { Component } from '../widgets/components';

const Employees:React.FC<{session:(value:boolean)=>void}> = ({session}) => {
    const endpoint = '/employees'
    const title = 'Employees'
    return (
        <Component title={title} endpoint={endpoint} session={session} />
    );
};

export default Employees;