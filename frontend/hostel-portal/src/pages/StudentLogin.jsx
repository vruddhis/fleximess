import { useState } from 'react'; //this is a hook

function StudentLogin(){
    const [username, setUsername] = useState(''); //passing initial blank state
    const [password, setPassword] = useState('');

    const handleChange = (e) => {
    const { name, value } = e.target; //key value pair
        
        if (name === 'username') {
            setUsername(value); 
        } else if (name === 'password') {
            setPassword(value);
        }
  };

    const handleSubmit = (e) => { 
        e.preventDefault(); //by default if html form submitted it reloads entire page
//the username state variable in the html is the value
//onChange is everytime a character is typed, so we need to write that function also

        console.log("sending login data ", { username, password })
        //will do hashing later
        //REST API here

    };
       

    return(
<div>
          <h2>Hostel Portal</h2>
          <p>Welcome to the hostel portal! Please login to your account.</p>
          <form onSubmit={handleSubmit}>
            <input type="text" name = "username" value={username} onChange={handleChange} /> 
            <input type="password" name="password" value={password} onChange={handleChange} /> 

            <button type="submit">Login</button>
            </form> 

</div>
    )

}

export default StudentLogin;